import datetime
from actions import BaseAction

class ActionDate(BaseAction):
	"""docstring for ActionDate."""
	def __init__(self):
		super(ActionDate, self).__init__()
		self.handled_classifier = "date"

	@classmethod
	def run(self, doc):
		print("Date: ", datetime.datetime.now().date().isoformat())

def getAction():
	return ActionDate()
