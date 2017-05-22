import datetime
from actions import BaseAction
import parsedatetime
import feedback

cal = parsedatetime.Calendar()

class ActionDate(BaseAction):
	"""docstring for ActionDate."""
	def __init__(self):
		super(ActionDate, self).__init__()
		self.handled_classifier = "date"

	@classmethod
	def run(self, doc):
		# print("Date: ", datetime.datetime.now().date().isoformat())
		sentence = next(doc.sents)
		target_date = datetime.datetime.now()
		query_type = None # valid: get, verify
		if sentence[0].text.lower() == "crystal":
			sentence = sentence[1:]
		if str(sentence.root.nbor(-1)) == "what":
			query_type = "get"
		else:
			query_type = "verify"
		print("query_type: ", query_type)

		if query_type == "get":
			parse_string = str(sentence[sentence.root.i:])
			print("parsing date: {}".format(parse_string))
			time_struct, parse_status = cal.parse(parse_string)
			if parse_status != 0:
				target_date = datetime.datetime(*time_struct[:6])
			else:
				print("parse_status: {}".format(parse_status))
			print("Date: ", target_date.date().isoformat())
			feedback.ShowNotify("Date: {}".format(target_date.date().isoformat()))
		elif query_type == "verify":
			compare_date = None

			# parse what we are looking in
			target_token = [word for word in sentence[sentence.root.i:] if word.ent_type_ == "DATE"][0]
			parse_string = str(target_token)
			print("parsing date: {}".format(parse_string))
			time_struct, parse_status = cal.parse(parse_string)
			if parse_status != 0:
				target_date = datetime.datetime(*time_struct[:6])
			else:
				print("parse_status: {}".format(parse_status))

			# parse what we are looking for
			parse_string = str([word for word in sentence[sentence.root.i:] if word != target_token])
			print("parsing date: {}".format(parse_string))
			yesterday_struct, _ = cal.parse("last week")
			time_struct, parse_status = cal.parse(parse_string, sourceTime=yesterday_struct)
			if parse_status != 0:
				compare_date = datetime.datetime(*time_struct[:6])
			else:
				print("parse_status: {}".format(parse_status))

			print("comparing dates - target: {}, compare: {}".format(target_date, compare_date))
			if compare_date.date() == target_date.date():
				feedback.ShowNotify("Yes")
			else:
				feedback.ShowNotify("No")
		else:
			feedback.OnStatus("error")
			feedback.ShowNotify("unknown query type: {}".format(query_type))

def getAction():
	return ActionDate()
