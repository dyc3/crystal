from actions import BaseAction
import utils

class ActionMediaPlay(BaseAction):
	"""docstring for ActionMediaPlay."""
	def __init__(self):
		super(ActionMediaPlay, self).__init__()
		self.handled_classifier = "media-play"

	@classmethod
	def run(self, doc):
		utils.runAndPrint("playerctl play")

def getAction():
	return ActionMediaPlay()
