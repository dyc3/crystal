from crystal.actions import BaseAction
import utils

class ActionMediaPause(BaseAction):
	"""docstring for ActionMediaPause."""
	def __init__(self):
		super(ActionMediaPause, self).__init__()
		self.handled_classifier = "media-pause"

	@classmethod
	def run(self, doc):
		utils.runAndPrint("playerctl pause")

def getAction():
	return ActionMediaPause()
