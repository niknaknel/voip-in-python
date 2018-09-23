from ttkthemes import themed_tk as tk
from Tkinter import *
import ttk
from math import floor
from threading import Thread
import time
from tkinterhtml import TkinterHtml

UBUNTU_ORANGE_100 = "#E95420"
UBUNTU_ORANGE_80 = "#ED764D"
GREEN_DARK = "#1F4820"
GREEN_LIGHT = "#2b602c"
RED_CHERRY = "#D33F3F"
RED_CHERRY_LIGHT = "#db4e4e"

TYPE_CALL = 0
TYPE_RECORD = 1

class ClientGUI:
    def __init__(self):
        self.SESSION_ACTIVE = False
        self.RECORDING_ACTIVE = False
        self.init_style()
        self.init_widgets()

    def init_style(self):
        self.root = tk.ThemedTk()
        self.root.get_themes()
        self.root.set_theme("radiance")

        windowWidth = self.root.winfo_reqwidth()
        windowHeight = self.root.winfo_reqheight()

        # Gets both half the screen width/height and window width/height
        positionRight = int(self.root.winfo_screenwidth() / 2 - windowWidth / 2)
        positionDown = int(self.root.winfo_screenheight() / 2 - windowHeight / 2)

        # Positions the window in the center of the page.
        self.root.geometry("+{}+{}".format(positionRight, positionDown))

        # images
        self.icon_send = PhotoImage(file="../img/icon_send.png")
        self.icon_record = PhotoImage(file="../img/icon_record.png")
        self.icon_call = PhotoImage(file="../img/icon_call.png")
        self.icon_end_call = PhotoImage(file="../img/icon_end_call.png")

    def init_widgets(self):

        # -- Labels -- #
        self.lbl_header = Label(self.root, text="Ready to make voice call.", bg=GREEN_DARK, fg='white')
        self.lbl_header.pack()

        # -- Buttons -- #
        self.btn_send = Button(self.root, image=self.icon_send, bg=UBUNTU_ORANGE_100, activebackground=UBUNTU_ORANGE_80)
        self.btn_call = Button(self.root, command=self.start_call, image=self.icon_call, bg=GREEN_DARK, activebackground=GREEN_LIGHT)
        self.btn_send.pack()
        self.btn_call.pack()

        # -- Input Area -- #
        self.input_content = StringVar()
        self.input_content.trace("w", lambda name, index, mode, sv=self.input_content: self.check_entry())
        self.entry_msg = Entry(self.root, textvariable=self.input_content)
        self.entry_msg.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def show(self):
        self.root.mainloop()

    def close(self):
        self.SESSION_ACTIVE = False
        self.RECORDING_ACTIVE = False

        self.root.destroy()

    def get_msg(self):
        # get input
        msg = self.entry_msg.get().strip()
        # clear input
        self.entry_msg.delete(0, END)
        return msg

    def check_entry(self):
        msg = self.entry_msg.get().strip()
        if len(msg) == 0:
            # change button functionality
            if not self.SESSION_ACTIVE:
                self.btn_send.configure(command=self.start_recording, image=self.icon_record)
        if len(msg) == 1:
            # change button functionality
            self.btn_send.configure(command=self.send_msg, image=self.icon_send)

    def send_msg(self):
        msg = self.get_msg()
        print(msg)

    def start_recording(self):
        self.RECORDING_ACTIVE = True
        self.repaint_recording()

        # time recording
        self.TIME_THREAD = Thread()
        self.TIME_THREAD = Thread(target=self.time_in, args=(TYPE_RECORD,))
        self.TIME_THREAD.setDaemon(True)
        self.TIME_THREAD.start()

        # start thread
        self.RECORD_THREAD = Thread()
        self.RECORD_THREAD = Thread(target=self.record)
        self.RECORD_THREAD.setDaemon(True)
        self.RECORD_THREAD.start()

    def record(self):
        while self.RECORDING_ACTIVE:
            print("recording...")
            time.sleep(1)
        return

    def stop_recording(self):
        self.RECORDING_ACTIVE = False
        self.repaint_recording()
        print("done!")

    def repaint_recording(self):
        if self.RECORDING_ACTIVE:
            self.btn_send.configure(command=self.stop_recording, bg=RED_CHERRY, activebackground=RED_CHERRY_LIGHT)
            self.btn_call.configure(state="disabled")
        else:
            self.btn_send.configure(command=self.start_recording, image=self.icon_send, bg=UBUNTU_ORANGE_100, activebackground=UBUNTU_ORANGE_80)
            self.lbl_header.configure(text="Recording stopped.", bg=GREEN_DARK)
            self.btn_call.configure(state="normal")
            self.check_entry()

    def time_in(self, type):
        duration = 0

        if type == TYPE_CALL:
            while self.SESSION_ACTIVE:
                out = "Call in progress (%s)" % self.format_time(duration)
                self.lbl_header.configure(text=out)
                time.sleep(1)
                duration += 1
            return

        elif type == TYPE_RECORD:
            while self.RECORDING_ACTIVE:
                out = "Recording voice message (%s)" % self.format_time(duration)
                self.lbl_header.configure(text=out)
                time.sleep(1)
                duration += 1
            return


    def start_call(self):
        self.SESSION_ACTIVE = True
        self.repaint_call()

        # time call
        self.TIME_THREAD = Thread()
        self.TIME_THREAD = Thread(target=self.time_in, args=(TYPE_CALL,))
        self.TIME_THREAD.setDaemon(True)
        self.TIME_THREAD.start()

        # start thread
        self.CALL_THREAD = Thread()
        self.CALL_THREAD = Thread(target=self.stream_call)
        self.CALL_THREAD.setDaemon(True)
        self.CALL_THREAD.start()

    def stream_call(self):
        while self.SESSION_ACTIVE:
            print("calling...")
            time.sleep(1)
        return

    def stop_call(self):
        self.SESSION_ACTIVE = False
        self.repaint_call()
        # end_call()
        print("call ended!")

    def repaint_call(self):
        if self.SESSION_ACTIVE:
            self.btn_call.configure(command=self.stop_call, image=self.icon_end_call, bg=GREEN_LIGHT, activebackground=RED_CHERRY)
        else:
            self.btn_call.configure(command=self.start_call, image=self.icon_call, bg=GREEN_DARK, activebackground=GREEN_LIGHT)
            self.lbl_header.configure(text="Call ended.", bg=GREEN_DARK)
            self.check_entry()

    def format_time(self, seconds):
        min = int(floor(seconds / 60))
        sec = seconds % 60

        return "{0:02}:{1:02}".format(min, sec)

if __name__=="__main__":
    ClientGUI().show()
