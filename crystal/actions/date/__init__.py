import datetime
from crystal.actions import BaseAction
from crystal.actions.responses import *
import parsedatetime
from crystal import feedback
import utils
import logging
log = logging.getLogger(__name__)

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
RELATIVE_DAYS = ["yesterday", "today", "tomorrow"]

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
	def find_target_and_compare_dates(self, doc, today=datetime.datetime.today()):
		"""
		Parses the sentence to extract 2 dates: the target date and the compare date.
		Returns the dates in a tuple: (target_date, compare_date)

		The target date refers to the date we are comparing.
		The compare date refers to the date that we use for context.

		For example, if the current date was Jan 1, 2000, and we parse the sentence:
		"How many days until January 2?"
		The target_date should be January 2, 2000, and
		the compare_date should be January 1, 2000

		Another example, if the current date was Jan 1, 2000, and we parse the sentence:
		"Is tomorrow Monday?"
		The target_date should be January 3, 2000 (the next Monday), and
		the compare_date should be January 2, 2000 (tomorrow)
		"""
		# FIXME: parsedatetime sucks ass, I should probably just try to parse the dates myself.
		target_date = None
		compare_date = None

		date_ents = [ent for ent in doc.ents if ent.label_ == "DATE" and not any([tok.lemma_ in ["day", "the", "many"] for tok in ent])]
		target_tokens = date_ents[-1]
		# HACK: "tomorrow <WEEKDAY>" gets misclassified as one entity
		if " " in target_tokens.lower_ and target_tokens.lower_.split()[0] == "tomorrow" and target_tokens.lower_.split()[1] in WEEKDAYS:
			compare_date = today + datetime.timedelta(days=1)
			target_date, _ = cal.parseDT(target_tokens.text.split()[1], sourceTime=today)
		elif len(date_ents) == 2 and all([ent.lower_ in WEEKDAYS + RELATIVE_DAYS for ent in date_ents]):
			compare_relative_delta = RELATIVE_DAYS.index(date_ents[0].lower_) - 1
			compare_date = today + datetime.timedelta(days=compare_relative_delta)
			if date_ents[0].lower_ == "tomorrow":
				target_date, _ = cal.parseDT(target_tokens.text, sourceTime=today)
			else:
				target_date, _ = cal.parseDT(target_tokens.text, sourceTime=compare_date - datetime.timedelta(days=7))
		else:
			target_date_text = target_tokens.text
			# HACK: parsedatetime doesn't parse ordinal numbers
			if any([target_date_text.lower().startswith(x) for x in MONTHS]):
				# HACK: ensure that the whole date is there, including the year
				if " " not in target_date_text and target_tokens[0].i + 1 < len(doc):
					target_date_text += f" {doc[target_tokens[0].i + 1]}"
					if target_tokens[0].i + 2 < len(doc) and doc[target_tokens[0].i + 2].like_num:
						target_date_text += f" {doc[target_tokens[0].i + 2].text}"
				month, day, *other = target_date_text.split()
				# HACK: make sure the year has 4 digits, because parsedatetime can't handle that
				if other:
					other[0] = other[0].zfill(4)
				day = utils.ordinal_to_int(day)
				target_date_text = " ".join([month, str(day), *other])
			target_date, _ = cal.parseDT(target_date_text, sourceTime=today)
			if len(date_ents) > 1:
				compare_date, _ = cal.parseDT(date_ents[0].text, sourceTime=today)
			else:
				compare_date = today

		time_reset = { "hour": 0, "minute": 0, "second": 0, "microsecond": 0 }
		target_date, compare_date = target_date.replace(**time_reset,), compare_date.replace(**time_reset)
		return target_date, compare_date

	@classmethod
	def verify(self, target_date: datetime.datetime, compare_date: datetime.datetime) -> bool:
		"""
		Check if the dates are equal.
		"""
		log.debug("comparing dates - target: {}, compare: {}".format(target_date, compare_date))
		return compare_date.date() == target_date.date()

	@classmethod
	def count(self, target_date: datetime.datetime, compare_date: datetime.datetime) -> int:
		"""
		Counts the number of days between the 2 dates.
		"""
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
			target_date, compare_date = self.find_target_and_compare_dates(doc)
			result = self.verify(target_date, compare_date)
			if result:
				return ActionResponseQuery("Yes")
			else:
				return ActionResponseQuery("No")
		elif query_type == "count":
			target_date, compare_date = self.find_target_and_compare_dates(doc)
			result = self.count(target_date, compare_date)
			return ActionResponseQuery("{} days".format(result))
		else:
			feedback.OnStatus("error")
			feedback.ShowNotify("unknown query type: {}".format(query_type))
			return ActionResponseBasic(ActionResponseType.FAILURE, "unknown query type: {}".format(query_type))

def getAction():
	return ActionDate()
