import datetime
from crystal.actions import BaseAction
from crystal.actions.responses import ActionResponseQuery
from crystal import feedback
import logging
log = logging.getLogger(__name__)

class ActionTime(BaseAction):
	"""docstring for ActionTime."""
	def __init__(self):
		super(ActionTime, self).__init__()
		self.handled_classifier = "time"

	@classmethod
	def parse(self, sentence):
		# TODO: implement grabing time from different timezones
		context_timezone = None # if None, use system's timezone
		target_timezone = None # if None, get the system time
		target_time = None # if None, get the current time

		return context_timezone, target_timezone, target_time

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		context_timezone, target_timezone, target_time = self.parse(sentence)

		current_time = datetime.datetime.now().time()
		log.info("Time: {}".format(current_time.isoformat()))
		return ActionResponseQuery(current_time.isoformat())

def getAction():
	return ActionTime()
