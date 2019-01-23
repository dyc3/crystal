import datetime
from crystal.actions import BaseAction
from crystal.actions.responses import *
import parsedatetime
from crystal import feedback
import logging
log = logging.getLogger(__name__)

cal = parsedatetime.Calendar()

class ActionDate(BaseAction):
	"""docstring for ActionDate."""
	def __init__(self):
		super(ActionDate, self).__init__()
		self.handled_classifier = "date"
		self.requires_updater = False

	@classmethod
	def get_query_type(self, sentence):
		for word in sentence:
			if word.lemma_ == "how" and word.nbor(1).lemma_ in ["many", "far"]:
				return "count"
			if word.lemma_ == "count":
				return "count"

			if word.lemma_ == "what":
				return "get"

		if sentence.root.lemma_ == "date":
			return "get"
		if sentence.root.lemma_ == "is":
			return "verify"
		if sentence.root.i != 0 and sentence.root.nbor(-1).lemma_ in ["what", "when"]:
			return "get"
		if sentence.root.lemma_ in ["what", "when"] or sentence[0].dep_ == "det":
			return "get"
		else:
			return "verify"

	@classmethod
	def find_target_and_compare_dates(self, sentence):
		target_date = None
		compare_date = None

		# parse what we are looking in
		target_token = [word for word in sentence if word.ent_type_ == "DATE" and word.lemma_ not in ["day", "the", "many"]][0]
		# the entity that the target token is in might have more than one word, eg. "Jan 20"
		# so make sure target_token has the *entire* date entity
		target_token = [ent for ent in sentence.doc.ents if ent.start == target_token.i][0].merge()

		parse_string = str(target_token)
		log.debug("parsing target date: {}".format(parse_string))
		time_struct, parse_status = cal.parse(parse_string)
		if parse_status != 0:
			target_date = datetime.datetime(*time_struct[:6])
		else:
			log.debug("parse_status: {}".format(parse_status))

		# parse what we are looking for
		parse_string = str([word for word in sentence if word != target_token])
		log.debug("parsing compare date: {}".format(parse_string))
		# ok, I'll admit this is really janky
		context_struct = None
		if target_date.date() == datetime.date.today() + datetime.timedelta(days=1):
			context_struct, _ = cal.parse("today")
		else:
			context_struct, _ = cal.parse("last week")
		log.debug("context: {}".format(context_struct))
		time_struct, parse_status = cal.parse(parse_string, sourceTime=context_struct)
		if parse_status != 0:
			compare_date = datetime.datetime(*time_struct[:6])
		else:
			log.debug("parse_status: {}".format(parse_status))

		# fallback
		if compare_date == None:
			log.debug("fallback, compare date == today")
			context_struct, _ = cal.parse("today")
			time_struct, parse_status = cal.parse(parse_string, sourceTime=context_struct)
			compare_date = datetime.datetime(*time_struct[:6])

		return target_date, compare_date

	@classmethod
	def verify(self, sentence):
		target_date, compare_date = self.find_target_and_compare_dates(sentence)
		log.debug("comparing dates - target: {}, compare: {}".format(target_date, compare_date))
		return compare_date.date() == target_date.date()

	@classmethod
	def count(self, sentence):
		target_date, compare_date = self.find_target_and_compare_dates(sentence)
		delta = target_date - compare_date
		return delta.days

	@classmethod
	def run(self, doc):
		# print("Date: ", datetime.datetime.now().date().isoformat())
		sentence = next(doc.sents)
		target_date = datetime.datetime.now()
		if str(sentence[0]).lower() == "crystal":
			sentence = sentence[1:]
		query_type = self.get_query_type(sentence) # valid: get, verify
		log.debug("query_type: {}".format(query_type))

		if query_type == "get":
			parse_string = str(sentence[sentence.root.i:])
			log.debug("parsing date: {}".format(parse_string))
			time_struct, parse_status = cal.parse(parse_string)
			if parse_status != 0:
				target_date = datetime.datetime(*time_struct[:6])
			else:
				log.debug("parse_status: {}".format(parse_status))

			date_str = target_date.date().strftime("%A, %Y-%b-%d")
			log.info("Date: {}".format(date_str))
			# feedback.ShowNotify("Date: {}".format(date_str))
			return ActionResponseQuery(date_str)
		elif query_type == "verify":
			result = self.verify(sentence)
			if result:
				return ActionResponseQuery("Yes")
			else:
				return ActionResponseQuery("No")
		elif query_type == "count":
			result = self.count(sentence)
			return ActionResponseQuery("{} days".format(result))
		else:
			feedback.OnStatus("error")
			feedback.ShowNotify("unknown query type: {}".format(query_type))
			return ActionResponseBasic(ActionResponseType.FAILURE, "unknown query type: {}".format(query_type))

def getAction():
	return ActionDate()
