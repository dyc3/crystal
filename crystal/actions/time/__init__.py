import datetime
from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import feedback
import utils
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

	def parse_target_time(self, doc, now=datetime.datetime.now()) -> datetime.datetime:
		all_time_ents = [ent for ent in doc.ents if ent.label_ == "TIME"]
		start_i = all_time_ents[0][0].i
		end_i = all_time_ents[-1][-1].i + 1
		seconds = utils.parse_duration_to_seconds(doc[start_i:end_i])
		return now + datetime.timedelta(seconds=seconds)

	def set_alarm(self, moment: datetime.datetime):
		self.state += [moment]

	def run(self, doc):
		command = self.parse(doc)

		if command == "check":
			current_time = datetime.datetime.now().time()
			log.info(f"Time: {current_time.isoformat()}")
			return ActionResponseQuery(current_time.isoformat())
		elif command == "set-alarm":
			moment = self.parse_target_time(doc)
			self.set_alarm(moment)
			self.save_state()
			delta = moment - datetime.datetime.now()
			return ActionResponseQuery(f"Set an alarm for {delta}")

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
