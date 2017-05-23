from actions import BaseAction
import utils

class ActionLockSystem(BaseAction):
	"""docstring for ActionLockSystem."""
	def __init__(self):
		super(ActionLockSystem, self).__init__()
		self.handled_classifier = "system-lock"

	@classmethod
	def run(self, doc):
		utils.runAndPrint("~/lock-screenshot.sh")

def getAction():
	return ActionLockSystem()
