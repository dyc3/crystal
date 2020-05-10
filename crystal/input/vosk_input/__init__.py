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
		self.realtime = True # indicates that audio can be streamed in

		self.model = Model("models/vosk-model-small-en-us-0.3")
		self.rec = None

	def process_audio(self, raw_audio: bytes, sample_rate: int, sample_width: int):
		if not self.rec:
			self.rec = KaldiRecognizer(self.model, sample_rate)
		full = self.rec.AcceptWaveform(raw_audio)
		if full:
			result = self.rec.Result()
		else:
			result = self.rec.PartialResult()
		result = json.loads(result)
		if "text" in result:
			text = result["text"]
		elif "partial" in result:
			text = result["partial"]
		if text:
			self.current_utterance = text
		return self.current_utterance

	def get_full_result(self):
		result = json.loads(self.rec.FinalResult())
		self.rec = None
		return result["text"]
