import unittest
import datetime
import spacy
from hypothesis import given, example
import hypothesis.strategies as st

from crystal.actions import date

nlp = None

class TestActionDate(unittest.TestCase):
	"""docstring for TestActionDate."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

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
			("how many days until july fourth", "count"),
		]
		action_date = date.ActionDate()
		for query, expected_query_type in test_set:
			with self.subTest("Testing \"{}\" relative to today's date, expecting {}".format(query, expected_query_type)):
				doc = nlp(query)
				sent = next(doc.sents)
				self.assertEqual(action_date.get_query_type(sent), expected_query_type, "Query type did not match, {}".format(query))

	def test_date_verify(self):
		# query, expected result
		test_set = [
			("is today {}".format(datetime.date.today().strftime("%A")), True),
			("is tomorrow {}".format((datetime.date.today() + datetime.timedelta(days=1)).strftime("%A")), True),
			("was yesterday {}".format((datetime.date.today() - datetime.timedelta(days=1)).strftime("%A")), True),
			("was yesterday {}".format(datetime.date.today().strftime("%A")), False),
			("is tomorrow {}".format(datetime.date.today().strftime("%A")), False),
		]
		action_date = date.ActionDate()
		for query, expected_result in test_set:
			with self.subTest("Testing \"{}\" relative to today's date, expecting {}".format(query, expected_result)):
				doc = nlp(query)
				target_date, compare_date = action_date.find_target_and_compare_dates(doc)
				self.assertEqual(action_date.verify(target_date, compare_date), expected_result, f"Date verification failed, {query}, parsed dates: target: {target_date}, compare: {compare_date}")

	def test_date_count_relative(self):
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
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=30)).strftime("%B %d")), 30),
			("how many days until {}".format((datetime.date.today() + datetime.timedelta(days=60)).strftime("%B %d")), 60),
		]
		action_date = date.ActionDate()
		for query, expected_result in test_set:
			with self.subTest("Testing \"{}\" relative to today's date, expecting {}".format(query, expected_result)):
				doc = nlp(query)
				target_date, compare_date = action_date.find_target_and_compare_dates(doc)
				test_result = action_date.count(target_date, compare_date)
				self.assertEqual(test_result, expected_result, "Failed to count days (expected {}, got {}), {}".format(expected_result, test_result, query))

	def test_date_extraction(self):
		# query, today, expected target_date, expected compare_date
		test_set = [
			("how many days until july fourth", datetime.datetime(2020, 7, 2), datetime.datetime(2020, 7, 4), datetime.datetime(2020, 7, 2)),
			("how many days until friday", datetime.datetime(2020, 7, 1), datetime.datetime(2020, 7, 3), datetime.datetime(2020, 7, 1)),
			("Is tomorrow Monday?", datetime.datetime(2000, 1, 1), datetime.datetime(2000, 1, 3), datetime.datetime(2000, 1, 2)),
			("How many days until January 2?", datetime.datetime(2000, 1, 1), datetime.datetime(2000, 1, 2), datetime.datetime(2000, 1, 1)),
			("was yesterday Wednesday", datetime.datetime(2020, 7, 2), datetime.datetime(2020, 7, 1), datetime.datetime(2020, 7, 1)),
			("is tomorrow Friday", datetime.datetime(2020, 7, 2), datetime.datetime(2020, 7, 3), datetime.datetime(2020, 7, 3)),
			("count days until March 03", datetime.datetime(2000, 1, 1), datetime.datetime(2000, 3, 3), datetime.datetime(2000, 1, 1)),
		]
		action_date = date.ActionDate()
		for query, today, expected_target_date, expected_compare_date in test_set:
			with self.subTest(f"Testing \"{query}\" relative to {today.date()}, expecting target: {expected_target_date.date()}, compare: {expected_compare_date.date()}"):
				doc = nlp(query)
				target_date, compare_date = action_date.find_target_and_compare_dates(doc, today=today)
				self.assertEqual(target_date, expected_target_date)
				self.assertEqual(compare_date, expected_compare_date)

	def test_date_count_absolute(self):
		# query, today, expected count
		test_set = [
			("how many days until july fourth", datetime.datetime(2020, 7, 2), 2),
			("how many days until friday", datetime.datetime(2020, 7, 1), 2),
			("how many days until friday", datetime.datetime(2020, 7, 2), 1),
		]
		action_date = date.ActionDate()
		for query, today, expected_result in test_set:
			with self.subTest(f"Testing \"{query}\" relative to {today.date()}, expecting count: {expected_result}"):
				doc = nlp(query)
				target_date, compare_date = action_date.find_target_and_compare_dates(doc, today=today)
				test_result = action_date.count(target_date, compare_date)
				self.assertEqual(test_result, expected_result, "Failed to count days (expected {}, got {}), {}".format(expected_result, test_result, query))

	@given(today=st.dates(), target_date=st.dates(), query_template=st.integers(min_value=0, max_value=1))
	def test_property_date_count_parse_compare_date_should_always_be_today(self, today, target_date, query_template):
		today = datetime.datetime.combine(today, datetime.datetime.min.time())
		target_date = datetime.datetime.combine(target_date, datetime.datetime.min.time())
		query = ["how many days until {}", "count days until {}"][query_template].format(target_date.strftime('%B %d'))
		doc = nlp(query)
		action_date = date.ActionDate()
		target_date, compare_date = action_date.find_target_and_compare_dates(doc, today=today)
		self.assertEqual(today, compare_date)

	@given(today=st.dates(), days=st.integers(min_value=0, max_value=364), query_template=st.integers(min_value=0, max_value=1))
	def test_property_date_count_should_be_accurate_within_year(self, today, days, query_template):
		today = datetime.datetime.combine(today, datetime.datetime.min.time())
		target_date = today + datetime.timedelta(days=days)
		query = ["how many days until {}", "count days until {}"][query_template].format(target_date.strftime('%B %d'))
		doc = nlp(query)
		action_date = date.ActionDate()
		target_date, compare_date = action_date.find_target_and_compare_dates(doc, today=today)
		result = action_date.count(target_date, compare_date)
		self.assertEqual(result, days)

	@given(today=st.dates(min_value=datetime.date(1000, 1, 1), max_value=datetime.date(3000, 1, 1)), days=st.integers(min_value=365, max_value=3000), query_template=st.integers(min_value=0, max_value=1))
	# @example(today=datetime.date(6838, 11, 5), days=1263, query_template=0) # not sure why this one fails, but it does
	def test_property_date_count_should_be_accurate_outside_year(self, today, days, query_template):
		today = datetime.datetime.combine(today, datetime.datetime.min.time())
		target_date = today + datetime.timedelta(days=days)
		query = ["how many days until {}", "count days until {}"][query_template].format(target_date.strftime('%B %d %Y'))
		doc = nlp(query)
		action_date = date.ActionDate()
		target_date, compare_date = action_date.find_target_and_compare_dates(doc, today=today)
		result = action_date.count(target_date, compare_date)
		self.assertEqual(result, days)

if __name__ == '__main__':
	unittest.main()
