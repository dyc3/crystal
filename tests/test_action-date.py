import unittest
import datetime
import spacy
from actions import date

nlp = None

class TestActionDate(unittest.TestCase):
	"""docstring for TestActionDate."""

	def setUp(self):
		global nlp
		nlp = spacy.load("en")

	def test_date_verify(self):
		# query, expected result
		test_set = [
			("is today {}".format(datetime.date.today().strftime("%A")), True),
			("is tomorrow {}".format((datetime.date.today() + datetime.timedelta(days=1)).strftime("%A")), True),
			("was yesterday {}".format(datetime.date.today().strftime("%A")), False),
			("is tomorrow {}".format(datetime.date.today().strftime("%A")), False),
		]
		action_date = date.ActionDate()
		for test, expectedResult in test_set:
			doc = nlp(test)
			sent = next(doc.sents)
			self.assertEqual(action_date.verify(sent), expectedResult)

if __name__ == '__main__':
	unittest.main()
