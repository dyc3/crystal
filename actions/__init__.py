from abc import ABCMeta

class BaseAction(metaclass=ABCMeta):
	"""docstring for BaseAction."""
	def __init__(self):
		super(BaseAction, self).__init__()
		self.handled_classifier = None

	@classmethod
	@abstractmethod
	def run(self, text):
		pass
