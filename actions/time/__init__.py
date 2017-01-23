import datetime
from actions import BaseAction

class ActionTime(BaseAction):
	"""docstring for ActionTime."""
	def __init__(self):
		super(ActionTime, self).__init__()
		self.handled_classifier = "time"

	@classmethod
	def run(self, doc):
		print("Time: ", datetime.datetime.now().time().isoformat())

def getAction():
	return ActionTime()
