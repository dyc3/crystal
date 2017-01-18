import pyaudio
import wave
import threading
from eventhook import EventHook

class MicrophoneInput(object):
	"""docstring for MicrophoneInput."""
	def __init__(self, chunk=1024, audioformat=pyaudio.paInt16, channels=2, rate=44100):
		super(MicrophoneInput, self).__init__()
		self.CHUNK = chunk
		self.FORMAT = audioformat
		self.CHANNELS = channels
		self.RATE = rate
		self.p = pyaudio.PyAudio()
		self.isRunning = False

		self.onFrame = EventHook()

	def Start(self):
		if not self.isRunning:
			self.threadRecord = threading.Thread(name="threadRecord")
			self.threadRecord.run = self._doThreadRecord
			self.isRunning = True
			self.threadRecord.start()
		else:
			print("Recording thread already started")

	def Stop(self):
		if self.isRunning:
			print("Stopping recording thread")
			self.isRunning = False
			self.threadRecord.join()
		else:
			print("Recording thread was not running")

	def _doThreadRecord(self):
		stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS,
						rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
		while self.isRunning:
			frame = stream.read(self.CHUNK)
			self.onFrame.fire(frame)

		stream.stop_stream()
		stream.close()
