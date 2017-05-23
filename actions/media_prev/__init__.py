from actions import BaseAction

class ActionMediaPrevious(BaseAction):
	"""docstring for ActionMediaPrevious."""
	def __init__(self):
		super(ActionMediaPrevious, self).__init__()
		self.handled_classifier = "media-prev"

	@classmethod
	def run(self, doc):
		utils.runAndPrint("playerctl previous")

def getAction():
	return ActionMediaPrevious()
