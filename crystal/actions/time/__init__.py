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
		self.requires_updater = True

		self.get_state()
		if self.state == None:
			self.state = []

	def parse(self, doc):
		for word in doc:
			if word.lemma_ in ["what", "time", "check"]:
				return "check"
			if word.lemma_ in ["set", "alarm", "timer"]:
				return "set-alarm"
		return "check"

	def set_alarm(self, moment: datetime.datetime):
		self.state += [moment]

	def run(self, doc):
		command = self.parse(doc)

		if command == "check":
			current_time = datetime.datetime.now().time()
			log.info("Time: {}".format(current_time.isoformat()))
			return ActionResponseQuery(current_time.isoformat())
		elif command == "set-alarm":
			self.set_alarm(datetime.datetime.now() + datetime.timedelta(seconds=5))
			self.save_state()
			return ActionResponseQuery("Set an alarm for 5 seconds")

	def update(self):
		alarms = self.state
		now = datetime.datetime.now()
		modified = False
		for moment in alarms:
			if now >= moment:
				log.info("Alarm triggered")
				alarms.remove(moment)
				modified = True
				feedback.ShowNotify("Alarm triggered")
		self.state = alarms
		if modified:
			self.save_state()

def getAction():
	return ActionTime()
