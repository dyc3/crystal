from eventhook import EventHook
from speech.base import BaseSpeechRecognizer

class GoogleSpeechRecognizer(BaseSpeechRecognizer):
	"""docstring for GoogleSpeechRecognizer."""
	def __init__(self, api_key):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished

		self.apikey = api_key
		self.streamingConfig = """
		{
			config: {
				language_code:"en-US",
				profanity_fither:false,
				max_alternatives:1
			}
		}
		"""

	def Start():
		pass

	def Stop():
		pass
