from crystal.input import BaseInput
import crystal.core
import time
from vosk import Model, KaldiRecognizer
import json
import logging
log = logging.getLogger(__name__)

# may require libgfortran?
# apt install libgfortran5

class VoskInput(BaseInput):
	""" Uses the `vosk` package to do speech recognition. """
	def __init__(self):
		super(VoskInput, self).__init__()
		self.current_utterance = ""

		self.model = Model("models/vosk-model-small-en-us-0.3")
		self.rec = KaldiRecognizer(self.model, 16000)

	def process_audio(self, raw_audio: bytes, sample_rate: int, sample_width: int):
		full = self.rec.AcceptWaveform(raw_audio)
		if full:
			result = self.rec.Result()
		else:
			result = self.rec.PartialResult()
		result = json.loads(result)
		if "text" in result:
			self.current_utterance = result["text"]
		elif "partial" in result:
			self.current_utterance = result["partial"]
		return self.current_utterance
