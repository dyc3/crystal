
class BaseInput(object):
	""" This is the class from which all input modules are derived from. """
	def __init__(self):
		super(BaseInput, self).__init__()
		# TODO: maybe have audio FFT available?

	def StartListening(self):
		""" Start listening for user input. """
		pass

	def StopListening(self):
		""" Stop listening for user input. """
		pass