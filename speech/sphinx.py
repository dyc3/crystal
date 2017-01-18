from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import threading
import audioop
from pocketsphinx import LiveSpeech, get_model_path

class SphinxSpeechRecognizer(BaseSpeechRecognizer):
	"""docstring for SphinxSpeechRecognizer."""
	def __init__(self, rate=44100, buffer_size=2048):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished
		self.isRunning = False
		self.status = "not-speaking"
		self._notSpeakingTicks = 0
		self.modal_path = get_model_path()

		self.speech = LiveSpeech(
			verbose=False,
			sampling_rate=rate,
			buffer_size=buffer_size,
			no_search=False,
			full_utt=False,
			hmm=os.path.join(model_path, 'en-us'),
			lm=os.path.join(model_path, 'en-us.lm.bin'),
			dic=os.path.join(model_path, 'cmudict-en-us.dict')
		)

	def Start(self):
		pass

	def Stop(self):
		pass

	def GiveFrame(self, frame, speaking_power=200):
		# TODO: finish this
		frame_power = audioop.rms(frame, 2)
		if self.status == "not-speaking" and frame_power >= speaking_power:
			self.status = "speaking"
			self._notSpeakingTicks = 0

		if self.status == "speaking":
			if frame_power >= speaking_power:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 80:
			self.status = "not-speaking"