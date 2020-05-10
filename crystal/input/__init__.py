
class BaseInput(object):
	""" This is the class from which all input modules are derived from. """
	def __init__(self):
		super(BaseInput, self).__init__()

	def process_audio(self, raw_audio: bytes, sample_rate: int, sample_width: int):
		"""
		Process the given audio input into text. raw_audio should be of type `bytes`
		"""
		pass