# Ideas for VoIP in Python

### Styling the GUI
ttk with themes: [ttkthemes](https://github.com/RedFantom/ttkthemes)

## Use `PyAudio` package

Home page: [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/)

**Example**
```
"""
PyAudio Example: Make a wire between input and output (i.e., record a
few samples and play them back immediately).
"""

import pyaudio

CHUNK = 1024
WIDTH = 2
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5

p = pyaudio.PyAudio()

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)

print("* recording")

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    stream.write(data, CHUNK)

print("* done")

stream.stop_stream()
stream.close()

p.terminate()
```

### Could we thread this?

**Example**
```
import...

p = pyaudio.PyAudio()
outgoing = Queue() #FIFO queue
dest = "none"

# One thread
def stream_audio():
    while True:
	if not queue.size() == 0:
	    chunk, dest = queue.pop()
	    send(chunk, dest) # function that sends chunk to specified destination
	else:
		time.sleep(0.5) # to lighten the load. Also acts as a buffer!

# Another thread (gui?)
def record(dest):
	stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)

	print("* recording")

	while hold:
		data = stream.read(CHUNK)
		outgoing.push(data, dest)

	print("* done")

	stream.stop_stream()
	stream.close()

def btn_record_presed(event=pressed):
	hold = True
	dest = get_dest() # get selected dest from gui
	record(dest)

def btn_record_released(event=released):
    hold = False

def send(data, dest):
	# do the UDP
	return

```

### Questions

>> Could we send control messages through the server? Is it necessary?

* How will the receiving be handled? (threading!)
	- incoming queue? (block during recording? or block recording during send? or mix recording and receiving)
* How can we implement voice note functionality?
	- recording type? seperate queues? Will this be blocking?
* How will the mixing be handled?
	- playback interface? pass all that need to be played to function which mixes it?
	- recv thead for each client or will server do the mixing?
	- is mixing only necessary in conference calls? If so, should it be done server side?

### Extra features
Which are essential?
	- padding
	- noise removal
	- normalization
	- silence detection (possibly use as recording trigger)

 **Maybe use**: [`rattelsnake`](https://github.com/loehnertz/rattlesnake)

### Experiments
* Measure latency for different chunk sizes (vs BUFFER)
* Measure latency/effects of different sample rates
* Measure noise levels

