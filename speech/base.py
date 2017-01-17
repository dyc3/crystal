from eventhook import EventHook

class BaseSpeechRecognizer(object):
	"""docstring for BaseSpeechRecognizer."""
	def __init__(self):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished

	def Start():
		pass

	def Stop():
		pass
