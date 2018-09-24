from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, error
from threading import Thread
import struct, errno, traceback, sys, time
from header import Header
import pyaudio, wave
from Queue import Queue

TYPE_CALL_REQUEST = 0
TYPE_TEXT = 1
TYPE_REC = 2
TYPE_CONTROL = 3

CODE_CALL_REFUSED = 0
CODE_LINE_BUSY = 1
CODE_CALL_ENDED = 2
CODE_CALL_ACCEPTED = 3

CHUNK = 1024
WIDTH = 2
CHANNELS = 1
RATE = 44100

peers = {}

class Client:
    def __init__(self):
        self.HOST = "localhost"
        self.PORT = 8000
        self.ADDR = (self.HOST, self.PORT)
        self.MYIP = self.my_ip()
        self.p = pyaudio.PyAudio()
        self.SESSION_ACTIVE = False
        self.incoming = Queue()
        self.outgoing = Queue()

        # tcp sock
        self.tcp_sock = socket(AF_INET, SOCK_STREAM)
        self.tcp_sock.bind(self.ADDR)

        self.tcp_sock.listen(1)
        print("Waiting for connection...\n")
        ACCEPT_THREAD = Thread(target=self.accept_connections)
        ACCEPT_THREAD.setDaemon(True)
        ACCEPT_THREAD.start()

        COMMAND_THREAD = Thread(target=self.prompt_input)
        COMMAND_THREAD.start()
        COMMAND_THREAD.join()

        #self.gui.top.mainloop()
        #self.tcp_sock.close()

    def conn(self, addr):
        """Connect to a peer"""
        # new thread?????
        try:
            # connect
            tcp_sock = socket(AF_INET, SOCK_STREAM)
            tcp_sock.connect(addr)

            RECEIVE_THREAD = Thread(target=self.receive, args=(tcp_sock, addr))
            RECEIVE_THREAD.start()
            RECEIVE_THREAD.join()

        except Exception as e:
            print(traceback.format_exc(e))

    def accept_connections(self):
        while True:
            # accept sender
            sender, sender_address = self.tcp_sock.accept()
            print("%s:%s has connected." % sender_address)

            peers[sender_address] = sender

            RECEIVE_THREAD = Thread(target=self.receive, args=(sender, sender_address))
            RECEIVE_THREAD.start()
            RECEIVE_THREAD.join()

    def receive(self, sender, sender_address):
        """Handles receiving of messages."""
        while True:
            try:
                header = self.recv_header(sender)
                type = header.msg_type

                if type == TYPE_CALL_REQUEST:
                    if self.SESSION_ACTIVE:
                        # refuse call
                        self.send(CODE_LINE_BUSY, TYPE_CONTROL, sender)
                        print("returned line busy")
                        return
                    else:
                        # refuse manually or accept
                        print("what else")

                        self.send(CODE_CALL_ACCEPTED, TYPE_CONTROL, sender)

                        CALL_THREAD = Thread(target=self.start_call, args=(sender_address,))
                        CALL_THREAD.setDaemon(True)
                        CALL_THREAD.start()


                elif type == TYPE_TEXT:
                    msg = self.recv_msg(sender)
                    print(msg)

                elif type == TYPE_REC:
                    # receive recording

                    # display in chat
                    print("%s:%s has sent you a recording!".format(sender_address))

                    # add to inbox (i.e. dict and update treeview)
                    print("Added to inbox")

                elif type == TYPE_CONTROL:
                    ctrl_msg = int(self.recv_msg(sender))
                    print(ctrl_msg)

                    if ctrl_msg == CODE_CALL_ENDED:
                        self.SESSION_ACTIVE = False

                    elif ctrl_msg == CODE_CALL_ACCEPTED:
                        self.start_call(sender_address)


            except error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(1)
                    print("No data available")
                    continue
                else:
                    print(traceback.format_exc())
                    sys.exit(1)


# ----------------------- Call functions --------------------------- #

    def place_call(self, sender_address):
        # get sender sock object
        dest = peers[sender_address]

        # send call request header
        header = Header(TYPE_CALL_REQUEST, self.MYIP)

        # send header
        s = header.serialize()
        dest.send(len(s))
        dest.send(s)

    def start_call(self, sender_address):
        self.SESSION_ACTIVE = True
        udp_sock = socket(AF_INET, SOCK_DGRAM)
        udp_sock.bind((sender_address))

        # stream my audio
        RECORD_AUDIO_THREAD = Thread(target=self.record_audio, args=(udp_sock, sender_address))
        RECORD_AUDIO_THREAD.setDaemon(True)
        RECORD_AUDIO_THREAD.start()

        # play incoming audio
        PLAY_INCOMING_AUDIO_THREAD = Thread(target=self.recv_incoming_stream, args=(udp_sock,))
        PLAY_INCOMING_AUDIO_THREAD.setDaemon(True)
        PLAY_INCOMING_AUDIO_THREAD.start()

    def record_audio(self, sock, address):
        stream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                             channels=CHANNELS,
                             rate=RATE,
                             input=True,
                             frames_per_buffer=CHUNK)

        print("* recording...")
        STREAM_THREAD = Thread(target=self.stream_audio, args=(sock, address))
        STREAM_THREAD.setDaemon(True)
        STREAM_THREAD.start()

        while self.SESSION_ACTIVE:
            data = stream.read(CHUNK)
            self.outgoing.put(data)

        print("* done")

        stream.stop_stream()
        stream.close()

    def stream_audio(self, sock, address):
        while True:
            if not self.outgoing.empty():
                data = self.outgoing.get()
                sock.sendto(data, address)
            else:
                time.sleep(0.2)  # to lighten the load. Also acts as a buffer!

    def recv_incoming_stream(self, sock):
        print("play incoming")
        stream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                             channels=CHANNELS,
                             rate=RATE,
                             output=True)

        # Either play (if call) or save (if recording)!!!!!
        PLAY_THREAD = Thread(target=self.play_incoming_audio, args=(stream,))
        PLAY_THREAD.setDaemon(True)
        PLAY_THREAD.start()

        frames = []
        while self.SESSION_ACTIVE:
            data = sock.recvfrom(CHUNK * CHANNELS * 2)[0]
            self.incoming.put(data)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        #self.save_wav("output.wav", frames)

    def play_incoming_audio(self, stream):
        BUFFER = 8
        while True:
            if self.incoming.qsize() == BUFFER:
                while True:
                    stream.write(self.incoming.get(), CHUNK)

    def save_wav(self, file_name, frames):
        print("writing %s to file" % file_name)
        FORMAT = pyaudio.paInt16

        wf = wave.open(file_name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

# ----------------------- Send functions --------------------------- #


    def send(self, msg, msg_code, dest):
        header = Header(msg_code, self.MYIP)

        # send header
        s = header.serialize()
        dest.send(len(s))
        dest.send(s)

        # send msg
        msg = str(msg)
        dest.send(len(msg))
        dest.send(msg)

# ----------------------- Recv functions --------------------------- #

    def recv_header(self, sock):
        raw = sock.recv(4)
        length = struct.unpack("!I", raw)[0]
        serial = self.recvall(sock, length)
        header = Header.deserialize(serial)
        return header

    def recv_msg(self, sock):
        raw = sock.recv(4)
        length = struct.unpack("!I", raw)[0]
        msg = self.recvall(sock, length)
        return msg

    def recvall(self, sock, length):
        buf = b''
        while length:
            new_buf = sock.recv(length)
            if not new_buf:
                break
            buf += new_buf
            length -= len(new_buf)
        return buf

# ----------------------- Helper functions --------------------------- #
    def my_ip(self):
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
        # from: Stackoverflow answer by Jamieson Becker
        #       https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib

    def prompt_input(self):
        cmd = ""
        while not cmd == "quit":
            cmd = raw_input()
            if "start call" in cmd:
                dest = cmd.split(' ')[2]
                addr = (dest.split(':')[0], dest.split(':')[1])
                self.place_call(addr)

        # safe release
        return

if __name__=="__main__":
    try:
        pb = int(sys.argv[1])
    except:
        print("Usage: python client.py playback (1 or 0)")
        sys.exit(1)

    Client()

