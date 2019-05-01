import datetime
from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import feedback
import logging
log = logging.getLogger(__name__)

class ActionTime(BaseAction):
	"""docstring for ActionTime."""
	def __init__(self):
		super(ActionTime, self).__init__()
		self.handled_classifier = "time"
		self.requires_updater = False

	@classmethod
	def parse(self, doc):
		for word in doc:
			if word.lemma_ in ["what", "time", "check"]:
				return "check"
			if word.lemma_ in ["set", "alarm"]:
				return "set-alarm"
		return "check"

	@classmethod
	def run(self, doc):
		command = self.parse(doc)

		if command == "check":
			current_time = datetime.datetime.now().time()
			log.info("Time: {}".format(current_time.isoformat()))
			return ActionResponseQuery(current_time.isoformat())
		elif command == "set-alarm":
			return ActionResponseBasic(ActionResponseType.FAILURE, "Can't do that yet")

def getAction():
	return ActionTime()
