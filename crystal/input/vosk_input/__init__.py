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
		self.__final_result = None

	def process_audio(self, raw_audio: bytes, sample_rate: int, sample_width: int):
		if not self.rec:
			self.rec = KaldiRecognizer(self.model, sample_rate)
		full = self.rec.AcceptWaveform(raw_audio)
		if full:
			result = self.rec.Result()
		else:
			result = self.rec.PartialResult()
		log.debug(result)
		result = json.loads(result)
		if "result" in result:
			self.__final_result = result
		if "text" in result:
			text = result["text"]
		elif "partial" in result:
			text = result["partial"]
		if text:
			self.current_utterance = text
		return self.current_utterance

	def get_full_result(self):
		if self.__final_result:
			result = self.__final_result
		else:
			result = self.rec.FinalResult()
			result = json.loads(result)
		log.debug(result)
		self.rec = None
		self.current_utterance = ""
		self.__final_result = None

		full_text = result["text"]
		# HACK: auto correct text to match domain vocabulary. Sorry.
		full_text = full_text.replace("palace music", "pause music")
		full_text = full_text.replace("applause music", "pause music")
		if "turn on" in full_text or "turn off" in full_text:
			full_text = full_text.replace("the land", "the lamp").replace("the lamb", "the lamp")
			if full_text.endswith("the lam"):
				full_text = full_text.replace("the lam", "the lamp")
		if full_text.endswith("to pm"):
			full_text = full_text.replace("to pm", "2 pm")
		if full_text.endswith(" a m"):
			full_text = full_text.replace(" a m", " am")
		if full_text.startswith("christo"):
			full_text = full_text.replace("christo", "crystal")

		return full_text
