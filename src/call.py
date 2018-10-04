from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, error
from threading import Thread
import struct
import errno, traceback
import sys
import time
from header import Header
import pyaudio
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
CHANNELS = 2
RATE = 44100

peers = {}

class Call:
    def __init__(self, playback=True):
        self.PEER_SOCK = socket(AF_INET, SOCK_STREAM)
        self.HOST = "localhost"
        self.PORT = 8000
        self.ADDR = (self.HOST, self.PORT)
        self.MYIP = self.my_ip()
        self.p = pyaudio.PyAudio()
        self.playback = playback
        self.SESSION_ACTIVE = False
        self.outgoing = Queue()

        # udp sock
        self.udp_sock = socket(AF_INET, SOCK_DGRAM)
        #self.udp_sock.bind(self.ADDR)

        CONNECT_THREAD = Thread(target=self.conn)
        CONNECT_THREAD.setDaemon(True)
        CONNECT_THREAD.start()

        COMMAND_THREAD = Thread(target=self.prompt_input)
        COMMAND_THREAD.start()
        COMMAND_THREAD.join()

    def conn(self):
        """Connect to router"""
        try:
            # connect
            self.PEER_SOCK.connect(self.ADDR)
            # initialize client
            self.start_call(self.ADDR)
        except Exception as e:
            print(traceback.format_exc(e))

    def record_audio(self, sock, address):
        stream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                             channels=CHANNELS,
                             rate=RATE,
                             input=True,
                             frames_per_buffer=CHUNK)

        STREAM_THREAD = Thread(target=self.stream_audio, args=(sock, address))
        STREAM_THREAD.setDaemon(True)
        STREAM_THREAD.start()

        while self.SESSION_ACTIVE:
            data = stream.read(CHUNK)
            print(time.time())
            self.outgoing.put(data)

        stream.stop_stream()
        stream.close()

    def stream_audio(self, sock, address):
        while self.SESSION_ACTIVE:
            if not self.outgoing.empty():
                data = self.outgoing.get()
                sock.sendto(data, address)
            else:
                time.sleep(0.1)

    # ----------------------- Call functions ---------------------- #

    def start_call(self, sender_address):
        self.SESSION_ACTIVE = True
        udp_sock = socket(AF_INET, SOCK_DGRAM)
        #udp_sock.bind((sender_address))

        # stream my audio
        STREAM_AUDIO_THREAD = Thread(target=self.record_audio, args=(udp_sock, sender_address))
        #STREAM_AUDIO_THREAD.setDaemon(True)
        STREAM_AUDIO_THREAD.start()

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
            cmd = raw_input("Waiting for input: ")
        # safe release
        self.SESSION_ACTIVE = False
        self.PEER_SOCK.send(struct.pack('!I', len("quit")))
        self.PEER_SOCK.send("quit")
        return

if __name__=="__main__":
    Call()
