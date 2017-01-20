import pyaudio
import wave
import threading
import numpy
import audioop
from eventhook import EventHook

class MicrophoneInput(object):
	"""docstring for MicrophoneInput."""
	def __init__(self, chunk=1024, audioformat=pyaudio.paInt16, channels=2, rate=16000, dynamic_power_threshold=True):
		super(MicrophoneInput, self).__init__()
		self.CHUNK = chunk
		self.FORMAT = audioformat
		self.CHANNELS = channels
		self.RATE = rate
		self.p = pyaudio.PyAudio()
		self.isRunning = False
		self.powerThreshold = 300
		self.dynamic_power_threshold = dynamic_power_threshold
		self.dynamic_power_adjustment_damping = 0.15
		self.dynamic_power_ratio = 1.5

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

	def Calibrate(self, duration=1): # TODO: rewrite this to be better
		stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
		elapsed_time = 0
		seconds_per_buffer = (self.CHUNK + 0.0) / self.RATE

		while True:
			elapsed_time += seconds_per_buffer
			if elapsed_time > duration: break
			buffer = stream.read(self.CHUNK)
			power = audioop.rms(buffer, 2)  # power of the audio signal

			# dynamically adjust the power threshold using asymmetric weighted average
			damping = self.dynamic_power_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
			target_power = power * self.dynamic_power_ratio
			self.powerThreshold = self.powerThreshold * damping + target_power * (1 - damping)

		stream.stop_stream()
		stream.close()

	def _doThreadRecord(self):
		stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS,
							 rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
		while self.isRunning:
			frame = stream.read(self.CHUNK)
			power = audioop.rms(frame, 2)

			if self.dynamic_power_threshold and power < self.powerThreshold:
				seconds_per_buffer = (self.CHUNK + 0.0) + self.RATE

				damping = self.dynamic_power_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
				target_power = power * self.dynamic_power_ratio
				self.powerThreshold = self.powerThreshold * damping + target_power * (1 - damping)

			self.onFrame.fire(frame, 2)

		stream.stop_stream()
		stream.close()
