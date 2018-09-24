
from ttkthemes import themed_tk as tk
import ttk
from Tkinter import *
from tkinterhtml import TkinterHtml
from PIL import Image, ImageTk

from math import floor
import hashlib
from threading import Thread
import time

UBUNTU_ORANGE_100 = "#E95420"
UBUNTU_ORANGE_80 = "#ED764D"
UBUNTU_LIGHT_GREY = "#F5F4F2"
GREEN_DARK = "#1F4820"
GREEN_LIGHT = "#2b602c"
RED_CHERRY = "#D33F3F"
RED_CHERRY_LIGHT = "#db4e4e"

WINDOW_SIZE = (600, 400)
TAB_WIDTH = WINDOW_SIZE[0]
TAB_HEIGHT = WINDOW_SIZE[1] - 28
SCALE_X = TAB_WIDTH/10
SCALE_Y = TAB_HEIGHT/7
ICON_SIZE = (48, 48)

TYPE_CALL = 0
TYPE_RECORD = 1

class ClientGUI:
    def __init__(self):
        self.init_style()
        self.init_widgets()

# ------------------ Text msg functions ------------------- #

    def get_msg(self):
        # get input
        msg = self.entryMsg.get().strip()
        # clear input
        self.entryMsg.delete(0, END)
        return msg

    def send_msg(self):
        msg = self.get_msg()
        print(msg)

# ------------------ Voice call functions ------------------- #

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
        print("calling...")
        while self.SESSION_ACTIVE:
            time.sleep(1)
        return

    def stop_call(self):
        self.SESSION_ACTIVE = False
        self.repaint_call()
        # end_call()

# ------------------ Voice recording functions ------------------- #

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
        print("recording...")
        while self.RECORDING_ACTIVE:
            time.sleep(1)
        return

    def stop_recording(self):
        self.RECORDING_ACTIVE = False
        self.repaint_recording()
        print("done!")

# ------------------ Audio playback functions ------------------- #

    def play_audio(self):
        self.PLAYING_RECORDING = True
        self.repaint_play_rec()

        while self.PLAYING_RECORDING and self.REC_PLAY_POS < self.progress['max']:
            time.sleep(1)
            self.REC_PLAY_POS += 1
            self.lblPlayPos.configure(text=self.format_time(self.REC_PLAY_POS))
            self.progress.step(1)

        self.PLAYING_RECORDING = False
        self.repaint_play_rec()

        if self.REC_PLAY_POS >= self.progress['max']:
            self.lblPlayPos.configure(text="00:00")

    def pause_audio(self):
        self.PLAYING_RECORDING = False
        self.repaint_play_rec()

# -------------------- TreeView handlers --------------------- #

    def get_tree_sel(self, field='text'):
        fields = {'Sender':0, 'Length':1, 'Size':2}

        if field in fields:
            idx = fields[field]
            vals = self.tree.item(self.tree.focus())['values']
            return str(vals[idx])

        return self.tree.item(self.tree.focus())[field]

    def tree_click(self, event=None):
        self.pause_audio()
        self.SELECTED_RECORDING = self.get_tree_sel()

    def tree_dbl_click(self, event=None):
        if not self.SELECTED_RECORDING == self.get_tree_sel():
            self.REC_PLAY_POS = 0

            # get selected rec length
            time = self.get_tree_sel('Length')
            len = self.format_time(time)
            self.progress.configure(max=len, value=0)

        self.SELECTED_RECORDING = self.get_tree_sel()

        # play recording
        self.PLAY_AUDIO_THREAD = Thread()
        self.PLAY_AUDIO_THREAD = Thread(target=self.play_audio)
        self.PLAY_AUDIO_THREAD.setDaemon(True)
        self.PLAY_AUDIO_THREAD.start()

# --------------------- GUI repainting ----------------------- #

    def repaint_call(self):
        if self.SESSION_ACTIVE:
            # disable recording playback
            self.pause_audio()
            self.btnPlayPause.configure(state="disabled")

            # repaint button and header
            self.btnCall.configure(command=self.stop_call, image=self.icon_end_call,
                                   bg=GREEN_LIGHT, activebackground=RED_CHERRY,
                                   highlightcolor=GREEN_LIGHT, highlightbackground=GREEN_LIGHT)
            self.lblHeader.configure(bg=GREEN_LIGHT)

            # disable recording function
            self.check_entry()
        else:
            # enable recording playbacks
            self.btnPlayPause.configure(state="normal")

            # repaint button and header
            self.btnCall.configure(command=self.start_call, image=self.icon_call,
                                   bg=GREEN_DARK, activebackground=GREEN_LIGHT,
                                   highlightcolor=GREEN_DARK, highlightbackground=GREEN_DARK)
            self.lblHeader.configure(text="Call ended.", bg=GREEN_DARK, highlightcolor=GREEN_DARK, highlightbackground=GREEN_DARK)

            # make recording function available
            self.check_entry()

    def repaint_recording(self):
        if self.RECORDING_ACTIVE:
            # disable recording playback
            self.pause_audio()
            self.btnPlayPause.configure(state="disabled")

            # repaint button and header
            self.btnSend.configure(command=self.stop_recording, bg=RED_CHERRY, activebackground=RED_CHERRY_LIGHT)
            self.lblHeader.configure(text="Recording stopped.", bg=RED_CHERRY)
            self.btnCall.configure(state="disabled")
        else:
            # enable recording playbacks
            self.btnPlayPause.configure(state="normal")

            # repaint button and header
            self.btnSend.configure(command=self.start_recording, image=self.icon_send, bg=UBUNTU_ORANGE_100, activebackground=UBUNTU_ORANGE_80)
            self.lblHeader.configure(text="Recording stopped.", bg=GREEN_DARK)
            self.btnCall.configure(state="normal")
            self.check_entry()

    def repaint_play_rec(self):
        if self.PLAYING_RECORDING:
            self.btnPlayPause.configure(image=self.icon_pause, command=self.pause_audio)
        else:
            if self.SESSION_ACTIVE or self.RECORDING_ACTIVE:
                self.btnPlayPause.configure(image=self.icon_play, command=self.tree_dbl_click, state="disabled")
            else:
                self.btnPlayPause.configure(image=self.icon_play, command=self.tree_dbl_click, state="normal")

# ----------------------- GUI reactivity ------------------------ #

    def time_in(self, type):
        duration = 0

        if type == TYPE_CALL:
            while self.SESSION_ACTIVE:
                out = "Call in progress (%s)" % self.format_time(duration)
                self.lblHeader.configure(text=out)
                time.sleep(1)
                duration += 1
            return

        elif type == TYPE_RECORD:
            while self.RECORDING_ACTIVE:
                out = "Recording voice message (%s)" % self.format_time(duration)
                self.lblHeader.configure(text=out)
                time.sleep(1)
                duration += 1
            return

    def check_entry(self):
        msg = self.entryMsg.get().strip()
        if len(msg) == 0:
            # change button functionality
            if self.SESSION_ACTIVE:
                self.btnSend.configure(command=self.send_msg(), image=self.icon_send)
            else:
                self.btnSend.configure(command=self.start_recording, image=self.icon_record)

        if len(msg) == 1:
            # change button functionality
            self.btnSend.configure(command=self.send_msg, image=self.icon_send)

# ---------------------- Helper functions ----------------------- #

    def format_time(self, arg):
        if type(arg) == int:
            min = int(floor(arg / 60))
            sec = arg % 60
            return "{0:02}:{1:02}".format(min, sec)

        elif type(arg) == str:
            min = int(arg.split(':')[0])
            sec = int(arg.split(':')[1])
            total = min*60 + sec
            return total

# --------------------- GUI instantiation ----------------------- #

    def init_style(self):
        self.root = tk.ThemedTk()
        self.root.get_themes()
        self.root.set_theme("radiance")

        self.root.title("VoIPPy")
        self.root.resizable(0, 0)
        self.root.geometry("%dx%d" % WINDOW_SIZE)

        windowWidth = self.root.winfo_reqwidth()
        windowHeight = self.root.winfo_reqheight()

        # Gets both half the screen width/height and window width/height
        positionRight = int(self.root.winfo_screenwidth() / 2 - windowWidth / 2)
        positionDown = int(self.root.winfo_screenheight() / 2 - windowHeight / 2)

        # Positions the window in the center of the page.
        self.root.geometry("+{}+{}".format(positionRight, positionDown))

        # images
        self.icon_send = ImageTk.PhotoImage(Image.open("../img/icon_send.png").resize(ICON_SIZE))
        self.icon_record = ImageTk.PhotoImage(Image.open("../img/icon_record.png").resize(ICON_SIZE))
        self.icon_call = ImageTk.PhotoImage(Image.open("../img/icon_call.png").resize(ICON_SIZE))
        self.icon_end_call = ImageTk.PhotoImage(Image.open("../img/icon_end_call.png").resize(ICON_SIZE))

        self.icon_play = ImageTk.PhotoImage(Image.open("../img/icon_play.png").resize((64, 64)))
        self.icon_pause = ImageTk.PhotoImage(Image.open("../img/icon_pause.png").resize((64, 64)))

        return

    def init_widgets(self):
        # -- Vars -- #
        self.SESSION_ACTIVE = False
        self.RECORDING_ACTIVE = False
        self.SELECTED_RECORDING = ""
        self.REC_PLAY_POS = 0
        self.PLAYING_RECORDING = False

        # -- Tabs -- #
        self.tabControl = ttk.Notebook(self.root)

        # main tab
        self.tabMain = ttk.Frame(self.tabControl, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1] - 15)
        self.tabControl.add(self.tabMain, text='Live chat')
        self.tabControl.pack(expand=True, fill="both")
        self.init_main_tab()

        # inbox tab
        self.tabInbox = ttk.Frame(self.tabControl, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1] - 15)
        self.tabControl.add(self.tabInbox, text='Inbox')
        self.tabControl.pack(expand=True, fill="both")
        self.init_inbox_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

        return

    def init_main_tab(self):
        # -- Labels -- #
        self.lblChannels = ttk.Label(self.tabMain, text="Channels", font=('Ubuntu', '18'), anchor=CENTER)
        self.lblHeader = Label(self.tabMain, text="Ready to make voice call.", bg=GREEN_DARK, fg='white')
        self.lblChannels.place(x=0, y=0, width=SCALE_X*3, height=SCALE_Y)
        self.lblHeader.place(x=SCALE_X*3, y=0, width=SCALE_X*6, height=SCALE_Y)

        # -- Buttons -- #
        self.btnCall = Button(self.tabMain, command=self.start_call, image=self.icon_call,
                              bg=GREEN_DARK, activebackground=GREEN_LIGHT,
                              highlightcolor=GREEN_DARK, highlightbackground=GREEN_DARK,
                              relief="flat")
        self.btnSend = Button(self.tabMain, image=self.icon_send, bg=UBUNTU_ORANGE_100, activebackground=UBUNTU_ORANGE_80)
        self.btnAddChannel = Button(self.tabMain, text="Add new channel")
        self.btnCall.place(x=SCALE_X*9, y=0, width=SCALE_X, height=SCALE_Y)
        self.btnSend.place(x=SCALE_X*9, y=SCALE_Y*6, width=SCALE_X, height=SCALE_Y)
        self.btnAddChannel.place(x=0, y=SCALE_Y*6, width=SCALE_X*3, height=SCALE_Y)

        # -- List Box -- #
        self.lbxChannels = Listbox(self.tabMain, name='listbox', selectmode=SINGLE)
        self.lbxChannels.grid(row=1, column=0, columnspan=3, rowspan=5)
        self.lbxChannels.place(x=0, y=SCALE_Y, width=SCALE_X*3, height=SCALE_Y*5)
        #self.lbxChannels.bind('<<ListboxSelect>>', self.select_contact)

        # -- Entry -- #
        self.inputContent = StringVar()
        self.inputContent.trace("w", lambda name, index, mode, sv=self.inputContent: self.check_entry())
        self.entryMsg = Entry(self.tabMain, textvariable=self.inputContent)
        self.entryMsg.place(x=SCALE_X*3, y=SCALE_Y*6, width=SCALE_X*6, height=SCALE_Y)

        # -- HTML display -- #
        self.displayHTML = TkinterHtml(self.tabMain)
        self.displayHTML.place(x=SCALE_X*3, y=SCALE_Y, width=SCALE_X*7, height=SCALE_Y*5)
        self.displayHTML.bind('<Button-1>', self.do_nothing)

        return

    def init_inbox_tab(self):
        # -- Label -- #
        self.lblChannels = ttk.Label(self.tabInbox, text="Recordings", font=('Ubuntu', '18'), anchor=CENTER)
        self.lblChannels.place(x=SCALE_X, y=0, width=SCALE_X * 8, height=SCALE_Y)

        # -- Button -- #
        self.btnPlayPause = Button(self.tabInbox, command=self.tree_dbl_click, image=self.icon_play,
                                   bg=UBUNTU_ORANGE_100, activebackground=UBUNTU_ORANGE_80,
                                   highlightcolor=UBUNTU_LIGHT_GREY, highlightbackground=UBUNTU_LIGHT_GREY,
                                   borderwidth=0, relief="flat", padx=0, pady=0, anchor=NW, state="disabled")
        self.btnPlayPause.place(x=int(SCALE_X*4.5), y=int(SCALE_Y*5.5), width=68, height=68)

        # -- Progress Bar -- #
        self.progress = ttk.Progressbar(self.tabInbox, orient="horizontal", length=SCALE_X*4, mode="determinate")
        self.progress.place(x=SCALE_X*3, y=int(SCALE_Y*4.8), height=floor(SCALE_Y/8))

        # seps & labels
        ttk.Separator(self.tabInbox, orient=VERTICAL).place(x=SCALE_X*3, y=SCALE_Y*5 - 18, height=20, width=3)
        ttk.Separator(self.tabInbox, orient=VERTICAL).place(x=SCALE_X*7+1, y=SCALE_Y*5 - 18, height=20, width=3)
        self.lblPlayPos = ttk.Label(self.tabInbox, text="00:00", anchor=CENTER)
        self.lblPlayPos.place(x=int(SCALE_X*4.7), y=SCALE_Y*5)

        # -- TreeView -- #
        self.tree = ttk.Treeview(self.tabInbox, columns=('Sender', 'Length', 'Size'), selectmode="browse")

        # label index
        self.tree.column('#0', width=SCALE_X*2)
        self.tree.heading('#0', text="Name")

        # label columns
        for col in self.tree['columns']:
            self.tree.column(col, width=SCALE_X, anchor=E)
            self.tree.heading(col, text=col)

        # adjust sender column size
        self.tree.column('Sender', width=SCALE_X * 2)

        # place tree
        self.tree.place(x=int(SCALE_X*0.5), y=SCALE_Y, width=SCALE_X*9, height=int(SCALE_Y*3.3))

        # bind tree
        self.tree.bind("<Button-1>", self.tree_click)
        self.tree.bind("<Double-1>", self.tree_dbl_click)

        # insert examples
        for i in range(186, 190):
            name = hashlib.sha1("%d010225" % i).hexdigest()[:5]
            self.tree.insert('','end', text='rec_%s' % name, values=('146.232.50.%d' % i, self.format_time((i-185)*10), '2.5MB'))

        return

    def show(self):
        self.root.mainloop()

    def do_nothing(self, event):
        return

    def close(self):
        self.SESSION_ACTIVE = False
        self.RECORDING_ACTIVE = False

        self.root.destroy()

# --------------------------------------------------------------- #

if __name__=="__main__":
    ClientGUI().show()
