from eventhook import EventHook
from crystal.input import BaseInput
import speech_recognition as sr
import time

class SpeechRecognitionInput(BaseInput):
	""" Uses the `SpeechRecognition` package to do speech recognition. """
	def __init__(self):
		super(SpeechRecognitionInput, self).__init__()
		self.on_utterance_start = EventHook()
		self.on_utterance_update = EventHook()
		self.on_utterance_finish = EventHook()
		self.current_utterance = ""

		self.recog = sr.Recognizer()
		self.mic = sr.Microphone()

	def StartListening(self):
		self.listener = Listener()
		# adjust for background noise
		with self.mic as source:
			self.recog.adjust_for_ambient_noise(source)
		self._do_stop_listening = self.recog.listen_in_background(self.mic, self.recognizerCallback)

	def StopListening(self):
		self._do_stop_listening()

	def recognizerCallback(recognizer, audio, failcount=0):
		try:
			self.on_utterance_start.fire()
			self.current_utterance = recognizer.recognize_google(audio)
			self.on_utterance_update.fire(self.current_utterance)
			self.on_utterance_finish.fire(self.current_utterance)
			self.current_utterance = ""
		except sr.UnknownValueError:
			print("sr.UnknownValueError")
		except sr.RequestError as e:
			if failcount < 3:
				waittime = 2 * failcount + 2
				print("retrying in {} seconds...".format(waittime))
				time.sleep(waittime)
			else:
				self.recognizerCallback(recognizer, audio, failcount + 1)
