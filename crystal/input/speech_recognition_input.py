from eventhook import EventHook
from crystal.input import BaseInput
import crystal.core
import speech_recognition as sr
import time
import logging
log = logging.getLogger(__name__)

class SpeechRecognitionInput(BaseInput):
	""" Uses the `SpeechRecognition` package to do speech recognition. """
	def __init__(self):
		super(SpeechRecognitionInput, self).__init__()
		# self.on_utterance_start = EventHook()
		# self.on_utterance_update = EventHook()
		# self.on_utterance_finish = EventHook()
		self.current_utterance = ""

		self.recog = sr.Recognizer()
		self.mic = sr.Microphone()

	def StartListening(self):
		# adjust for background noise
		with self.mic as source:
			self.recog.adjust_for_ambient_noise(source)
		self._do_stop_listening = self.recog.listen_in_background(self.mic, self.recognizerCallback)

	def StopListening(self):
		if not self._do_stop_listening:
			self._do_stop_listening()

	def recognizerCallback(self, recognizer, audio, failcount=0):
		crystal.core.on_utterance_start.fire()
		try:
			response = recognizer.recognize_google(audio, show_all=True)
			if not str(response) == "[]":
				self.current_utterance = self.pickMostLikelyRecognition(response['alternative'])
		except sr.UnknownValueError:
			# This happens when no speech is recognized in the audio, so
			# just eat the error and ignore it.
			return
		except sr.RequestError:
			if failcount < 3:
				waittime = 2 * failcount + 2
				log.debug("retrying in {} seconds...".format(waittime))
				time.sleep(waittime)
				self.recognizerCallback(recognizer, audio, failcount + 1)
			return

		if not self.current_utterance == "":
			crystal.core.on_utterance_update.fire(self.current_utterance)
			crystal.core.on_utterance_finish.fire(self.current_utterance)
		self.current_utterance = ""

	def pickMostLikelyRecognition(self, recognitions):
		"""
		This shit janky af, would not recommend. It would be preferable to supply "context" in some way,
		and pick the recognitions using the context.

		The purpose of this method is to weed out any misrecognized speech that would trip up parsing.
		Sorry, but it's the easiest way, and its better than using .replace() on request text.
		"""

		scores = []

		for r in recognitions:
			score = 0
			text = r["transcript"]

			# this is janky af and makes me sad
			bad_crystal_aliases = ["Krystal","Kristal","Cristal","Chrystal","Coastal","Chris","Kris"]
			bad_proper_nouns = ["Creek","Roller","Run","Focus","Clinic","Quinn","Gym Leaders","Kimi","Timmy",
								"Kimmy","Define","Rangel","Ringle"]
			if any((alias in text or alias.lower()) for alias in bad_crystal_aliases):
				score -= 1
				if any("{} quick".format(alias) == text for alias in bad_crystal_aliases): score -= 1
				if any("{} {}".format(alias, bad) in text for alias in bad_crystal_aliases for bad in bad_proper_nouns): score -= 1
			if "Crystal quick" in text: score -= 1
			if any("Crystal {}".format(bad) in text for bad in bad_proper_nouns): score -= 1
			if "default sync" in text: score -= 1
			if "work Space Nine" in text: score -= 2
			if "focusrite" in text: score -= 1
			if text.endswith("workspace for"): score -= 1
			if text.endswith("desktop for"): score -= 1
			if text.endswith("the stock for"): score -= 1
			if text.endswith(" for"): score -= 1
			if text.endswith("clothes that"): score -= 1
			if text.endswith("close at"): score -= 1
			if "work space" in text: score -= 1
			if "wurkspace" in text: score -= 1 # what the fuck even is this?
			if "Works face for" in text: score -= 1
			if "ShowMe" in text: score -= 1
			if "show me the top five" in text: score -= 1
			if "open up at home" in text: score -= 1
			if "open up Adam" in text: score -= 1
			if "run Adam" in text: score -= 1
			if "Paws video" in text: score -= 1
			if "paws" in text: score -= 1
			if "cromeans" in text: score -= 1
			if "move Vista" in text: score -= 1
			if "mufassal" in text: score -= 1
			if "Crystal Puzzle" in text: score -= 1
			if "Crystal Palace" in text: score -= 1

			if text.lower().startswith("crystal"):
				score += 1
				if "Crystal click" in text: score += 1
				if "Crystal quit" in text: score += 1
			if "open up atom" in text: score += 1
			if "run atom" in text: score += 1
			if "workspace 4" in text: score += 1
			if "workspace 9" in text: score += 1
			if "desktop 5" in text: score += 1
			if "desktop 10" in text: score += 1
			if "close that" in text: score += 1
			if "default sink" in text: score += 1
			if "fullscreen" in text: score += 1
			if "switch chromium's audio" in text: score += 1

			scores.append((text, score))

		# print("SORTED:", sorted(scores, key=lambda textscore: textscore[1], reverse=True))
		transcript = sorted(scores, key=lambda textscore: textscore[1], reverse=True)[0][0]
		return transcript
