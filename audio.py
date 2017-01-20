import pyaudio
import wave
import threading
import numpy
import audioop
import shutil
import subprocess
import os
import stat
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
		self.sample_width = self.p.get_sample_size(self.FORMAT)
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
			power = audioop.rms(buffer, self.sample_width)  # power of the audio signal

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
			power = audioop.rms(frame, self.sample_width)

			if self.dynamic_power_threshold and power < self.powerThreshold:
				seconds_per_buffer = (self.CHUNK + 0.0) + self.RATE

				damping = self.dynamic_power_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
				target_power = power * self.dynamic_power_ratio
				self.powerThreshold = self.powerThreshold * damping + target_power * (1 - damping)

			self.onFrame.fire(frame, self.sample_width)

		stream.stop_stream()
		stream.close()

def get_flac_converter():
	"""Returns the absolute path of a FLAC converter executable, or raises an OSError if none can be found."""
	flac_converter = shutil.which("flac")  # check for installed version first
	if flac_converter is None:  # flac utility is not installed
		base_path = os.path.dirname(os.path.abspath(__file__))  # directory of the current module file, where all the FLAC bundled binaries are stored
		system, machine = platform.system(), platform.machine()
		if system == "Windows" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
			flac_converter = os.path.join(base_path, "flac-win32.exe")
		elif system == "Darwin" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
			flac_converter = os.path.join(base_path, "flac-mac")
		elif system == "Linux" and machine in {"i686", "i786", "x86"}:
			flac_converter = os.path.join(base_path, "flac-linux-x86")
		elif system == "Linux" and machine in {"x86_64", "AMD64"}:
			flac_converter = os.path.join(base_path, "flac-linux-x86_64")
		else:  # no FLAC converter available
			raise OSError("FLAC conversion utility not available - consider installing the FLAC command line application by running `apt-get install flac` or your operating system's equivalent")

	# mark FLAC converter as executable if possible
	try:
		stat_info = os.stat(flac_converter)
		os.chmod(flac_converter, stat_info.st_mode | stat.S_IEXEC)
	except OSError: pass

	return flac_converter

def get_raw_data(self, frame, sample_rate, sample_width, convert_rate=None, convert_width=None):
	"""
	Returns a byte string representing the raw frame data given.
	If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.
	If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.
	Writing these bytes directly to a file results in a valid `RAW/PCM audio file <https://en.wikipedia.org/wiki/Raw_audio_format>`__.
	"""
	assert convert_rate is None or convert_rate > 0, "Sample rate to convert to must be a positive integer"
	assert convert_width is None or (convert_width % 1 == 0 and 1 <= convert_width <= 4), "Sample width to convert to must be between 1 and 4 inclusive"

	raw_data = frame

	# make sure unsigned 8-bit audio (which uses unsigned samples) is handled like higher sample width audio (which uses signed samples)
	if self.sample_width == 1:
		raw_data = audioop.bias(raw_data, 1, -128)  # subtract 128 from every sample to make them act like signed samples

	# resample audio at the desired rate if specified
	if convert_rate is not None and sample_rate != convert_rate:
		raw_data, _ = audioop.ratecv(raw_data, sample_width, 1, sample_rate, convert_rate, None)

	# convert samples to desired sample width if specified
	if convert_width is not None and sample_width != convert_width:
		if convert_width == 3:  # we're converting the audio into 24-bit (workaround for https://bugs.python.org/issue12866)
			raw_data = audioop.lin2lin(raw_data, sample_width, 4)  # convert audio into 32-bit first, which is always supported
			try: audioop.bias(b"", 3, 0)  # test whether 24-bit audio is supported (for example, ``audioop`` in Python 3.3 and below don't support sample width 3, while Python 3.4+ do)
			except audioop.error:  # this version of audioop doesn't support 24-bit audio (probably Python 3.3 or less)
				raw_data = b"".join(raw_data[i + 1:i + 4] for i in range(0, len(raw_data), 4))  # since we're in little endian, we discard the first byte from each 32-bit sample to get a 24-bit sample
			else:  # 24-bit audio fully supported, we don't need to shim anything
				raw_data = audioop.lin2lin(raw_data, sample_width, convert_width)
		else:
			raw_data = audioop.lin2lin(raw_data, sample_width, convert_width)

	# if the output is 8-bit audio with unsigned samples, convert the samples we've been treating as signed to unsigned again
	if convert_width == 1:
		raw_data = audioop.bias(raw_data, 1, 128)  # add 128 to every sample to make them act like unsigned samples again

	return raw_data

def get_wav_data(self, frame, sample_rate, sample_width, convert_rate=None, convert_width=None):
	"""
	Returns a byte string representing the contents of a WAV file containing the given frame.
	If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.
	If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.
	Writing these bytes directly to a file results in a valid `WAV file <https://en.wikipedia.org/wiki/WAV>`__.
	"""
	raw_data = get_raw_data(frame, sample_rate, sample_width, convert_rate, convert_width)
	sample_rate = sample_rate if convert_rate is None else convert_rate
	sample_width = sample_width if convert_width is None else convert_width

	# generate the WAV file contents
	with io.BytesIO() as wav_file:
		wav_writer = wave.open(wav_file, "wb")
		try:  # note that we can't use context manager, since that was only added in Python 3.4
			wav_writer.setframerate(sample_rate)
			wav_writer.setsampwidth(sample_width)
			wav_writer.setnchannels(1)
			wav_writer.writeframes(raw_data)
			wav_data = wav_file.getvalue()
		finally:  # make sure resources are cleaned up
			wav_writer.close()
	return wav_data

def get_flac_data(frame, sample_rate, sample_width, convert_rate=None, convert_width=None):
	"""
	Returns a byte string representing the contents of a FLAC file converted from the given frame.
	Note that 32-bit FLAC is not supported. If the audio data is 32-bit and ``convert_width`` is not specified, then the resulting FLAC will be a 24-bit FLAC.
	If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.
	If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.
	Writing these bytes directly to a file results in a valid `FLAC file <https://en.wikipedia.org/wiki/FLAC>`__.
	"""
	assert convert_width is None or (convert_width % 1 == 0 and 1 <= convert_width <= 3), "Sample width to convert to must be between 1 and 3 inclusive"

	if sample_width > 3 and convert_width is None:  # resulting WAV data would be 32-bit, which is not convertable to FLAC using our encoder
		convert_width = 3  # the largest supported sample width is 24-bit, so we'll limit the sample width to that

	# run the FLAC converter with the WAV data to get the FLAC data
	wav_data = get_wav_data(frame, sample_rate, sample_width, convert_rate, convert_width)
	flac_converter = get_flac_converter()
	process = subprocess.Popen([
		flac_converter,
		"--stdout", "--totally-silent",  # put the resulting FLAC file in stdout, and make sure it's not mixed with any program output
		"--best",  # highest level of compression available
		"-",  # the input FLAC file contents will be given in stdin
	], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	flac_data, stderr = process.communicate(wav_data)
	return flac_data
