import unittest
import datetime
import spacy
from crystal.actions import date

nlp = None

class TestActionDate(unittest.TestCase):
	"""docstring for TestActionDate."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_get_query_type(self):
		# query, expected query type
		test_set = [
			("what day is it", "get"),
			("tell me what day it is", "get"),
			("what's the date", "get"),
			("date", "get"),

			("is today Monday", "verify"),
			("is tomorrow Monday", "verify"),
			("was yesterday Monday", "verify"),
			("is tomorrow Monday", "verify"),

			("how many days until Monday", "count"),
			("count the days til Friday", "count"),
		]
		action_date = date.ActionDate()
		for query, expected_query_type in test_set:
			with self.subTest():
				doc = nlp(query)
				sent = next(doc.sents)
				self.assertEqual(action_date.get_query_type(sent), expected_query_type, "Query type did not match, {}".format(query))

	def test_date_verify(self):
		# query, expected result
		test_set = [
			("is today {}".format(datetime.date.today().strftime("%A")), True),
			("is tomorrow {}".format((datetime.date.today() + datetime.timedelta(days=1)).strftime("%A")), True),
			("was yesterday {}".format(datetime.date.today().strftime("%A")), False),
			("is tomorrow {}".format(datetime.date.today().strftime("%A")), False),
		]
		action_date = date.ActionDate()
		for query, expected_result in test_set:
			with self.subTest():
				doc = nlp(query)
				sent = next(doc.sents)
				self.assertEqual(action_date.verify(sent), expected_result, "Date verification failed, {}".format(query))

	def test_date_count(self):
		# query, expected result
		test_set = [
			# test relative terms
			("how many days until today", 0),
			("how many days until tomorrow", 1),
			("how many days until yesterday", -1),

			# test week days
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=1)).strftime("%A")), 1),
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=4)).strftime("%A")), 4),

			# test specific dates
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=15)).strftime("%B %d")), 15),
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=5)).strftime("%B %d")), 5),
		]
		action_date = date.ActionDate()
		for query, expected_result in test_set:
			with self.subTest():
				doc = nlp(query)
				sent = next(doc.sents)
				test_result = action_date.count(sent)
				self.assertEqual(test_result, expected_result, "Failed to count days (expected {}, got {}), {}".format(expected_result, test_result, query))

if __name__ == '__main__':
	unittest.main()
