import datetime
from crystal.actions import BaseAction
import parsedatetime
from crystal import feedback

cal = parsedatetime.Calendar()

class ActionDate(BaseAction):
	"""docstring for ActionDate."""
	def __init__(self):
		super(ActionDate, self).__init__()
		self.handled_classifier = "date"

	@classmethod
	def get_query_type(self, sentence):
		if sentence.root.lemma_ == "is":
			return "verify"
		if sentence.root.lemma_ in ["what", "when"] or sentence.root.nbor(-1).lemma_ in ["what", "when"] or sentence[0].dep_ == "det":
			return "get"
		else:
			return "verify"

	@classmethod
	def verify(self, sentence):
		target_date = None
		compare_date = None

		# parse what we are looking in
		target_token = [word for word in sentence[sentence.root.i:] if word.ent_type_ == "DATE"][0]
		parse_string = str(target_token)
		print("parsing target date: {}".format(parse_string))
		time_struct, parse_status = cal.parse(parse_string)
		if parse_status != 0:
			target_date = datetime.datetime(*time_struct[:6])
		else:
			print("parse_status: {}".format(parse_status))

		# parse what we are looking for
		parse_string = str([word for word in sentence[sentence.root.i:] if word != target_token])
		print("parsing compare date: {}".format(parse_string))
		# ok, I'll admit this is really janky
		context_struct = None
		if target_date.date() == datetime.date.today() + datetime.timedelta(days=1):
			context_struct, _ = cal.parse("today")
		else:
			context_struct, _ = cal.parse("last week")
		print("context: ", context_struct)
		time_struct, parse_status = cal.parse(parse_string, sourceTime=context_struct)
		if parse_status != 0:
			compare_date = datetime.datetime(*time_struct[:6])
		else:
			print("parse_status: {}".format(parse_status))

		print("comparing dates - target: {}, compare: {}".format(target_date, compare_date))
		return compare_date.date() == target_date.date()

	@classmethod
	def run(self, doc):
		# print("Date: ", datetime.datetime.now().date().isoformat())
		sentence = next(doc.sents)
		target_date = datetime.datetime.now()
		if str(sentence[0]).lower() == "crystal":
			sentence = sentence[1:]
		query_type = self.get_query_type(sentence) # valid: get, verify
		print("query_type: ", query_type)

		if query_type == "get":
			parse_string = str(sentence[sentence.root.i:])
			print("parsing date: {}".format(parse_string))
			time_struct, parse_status = cal.parse(parse_string)
			if parse_status != 0:
				target_date = datetime.datetime(*time_struct[:6])
			else:
				print("parse_status: {}".format(parse_status))

			date_str = target_date.date().strftime("%A, %Y-%b-%d")
			print("Date: ", date_str)
			feedback.ShowNotify("Date: {}".format(date_str))
			return "Date: {}".format(date_str)
		elif query_type == "verify":
			result = self.verify(sentence)
			if result:
				feedback.ShowNotify("Yes")
			else:
				feedback.ShowNotify("No")
			return result
		else:
			feedback.OnStatus("error")
			feedback.ShowNotify("unknown query type: {}".format(query_type))

def getAction():
	return ActionDate()
