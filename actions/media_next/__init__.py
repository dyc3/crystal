from actions import BaseAction
import utils

class ActionMediaNext(BaseAction):
	"""docstring for ActionMediaNext."""
	def __init__(self):
		super(ActionMediaNext, self).__init__()
		self.handled_classifier = "media-next"

	@classmethod
	def run(self, doc):
		utils.runAndPrint("playerctl next")

def getAction():
	return ActionMediaNext()
