import datetime
import parsedatetime
from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import feedback
import utils
import logging
log = logging.getLogger(__name__)

ACTION_CHECK = "check"
ACTION_SET = "set"
TARGET_TIME = "time"
TARGET_ALARM = "alarm"

cal = parsedatetime.Calendar()

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
		action = ACTION_CHECK
		target = TARGET_TIME

		if utils.find_word(doc, ["what", "give", "check", "list", "show"]):
			action = ACTION_CHECK
		elif utils.find_word(doc, ["set", "create", "make", "start"]):
			action = ACTION_SET

		if utils.find_word(doc, ["time"]):
			target = TARGET_TIME
		elif utils.find_word(doc, ["alarm", "timer", "alert"]):
			target = TARGET_ALARM

		return action, target

	def parse_target_time(self, doc, now=datetime.datetime.now()) -> datetime.datetime:
		if utils.find_word(doc, ["hour", "minute", "second"]):
			all_time_ents = [ent for ent in doc.ents if ent.label_ == "TIME"]
			start_i = all_time_ents[0][0].i
			end_i = all_time_ents[-1][-1].i + 1
			seconds = utils.parse_duration_to_seconds(doc[start_i:end_i])
			return now + datetime.timedelta(seconds=seconds)
		else:
			all_time_ents = [ent for ent in doc.ents if ent.label_ == "CARDINAL" or ent.label_ == "TIME"]
			if len(all_time_ents) > 0:
				start_i = all_time_ents[0][0].i
				end_i = all_time_ents[-1][-1].i + 1
			else:
				num_tokens = [token for token in doc if token.like_num or token.text in ["am", "pm"]]
				start_i = num_tokens[0].i
				end_i = num_tokens[-1].i + 1
			if utils.find_word(doc, ["am", "pm"]):
				target_time, _ = cal.parseDT(doc[start_i:end_i].text, sourceTime=now)
			else:
				target_time = now.replace(hour=(utils.text2int(doc[start_i:end_i].text) + 12*(now.hour < 12)) % 24, minute=0, second=0, microsecond=0)
			if target_time < now:
				target_time += datetime.timedelta(days=1)
			return target_time

	def set_alarm(self, moment: datetime.datetime):
		self.state += [moment]

	def run(self, doc):
		action, target = self.parse(doc)

		if target == TARGET_TIME:
			if action == ACTION_CHECK:
				current_time = datetime.datetime.now().time()
				log.info(f"Time: {current_time.isoformat()}")
				return ActionResponseQuery(current_time.isoformat())
			else:
				return ActionResponseBasic(ActionResponseType.FAILURE, f"I don't know how to {action} the time.")
		elif target == TARGET_ALARM:
			if action == ACTION_CHECK:
				return ActionResponseQueryList("Alarms and timers", self.state)
			elif action == ACTION_SET:
				now = datetime.datetime.now()
				moment = self.parse_target_time(doc, now)
				if moment < now:
					return ActionResponseBasic(ActionResponseType.FAILURE, f"Failed to set alarm because the calculated alarm time was in the past. moment={moment}, now={now}")
				self.set_alarm(moment)
				self.save_state()
				delta = moment - now
				return ActionResponseQuery(f"Set an alarm for {delta}")
			else:
				return ActionResponseBasic(ActionResponseType.FAILURE, f"I don't know how to {action} the alarms.")
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, f"I don't know how to perform: \"{action}\" on the target \"{target}\".")

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
