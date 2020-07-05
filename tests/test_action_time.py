import unittest
import spacy
import datetime
from hypothesis import given, example
import hypothesis.strategies as st

from crystal.actions import time

nlp = None

class TestActionTime(unittest.TestCase):
	"""docstring for TestActionTime."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_time_parse(self):
		# query, action, target
		test_set = [
			("what is the time", (time.ACTION_CHECK, time.TARGET_TIME)),
			("what's the time", (time.ACTION_CHECK, time.TARGET_TIME)),
			("what time is it", (time.ACTION_CHECK, time.TARGET_TIME)),
			("give me the time", (time.ACTION_CHECK, time.TARGET_TIME)),

			("set an alarm for 9 AM", (time.ACTION_SET, time.TARGET_ALARM)),
			("set an alarm for 7", (time.ACTION_SET, time.TARGET_ALARM)),
			("create an alarm for 8", (time.ACTION_SET, time.TARGET_ALARM)),
			("set a timer for 8 minutes", (time.ACTION_SET, time.TARGET_ALARM)),
		]
		action_time = time.ActionTime()
		for test, expected in test_set:
			doc = nlp(test)
			result = action_time.parse(doc)
			self.assertEqual(result, expected)

	@given(now=st.datetimes(), hours=st.integers(min_value=0, max_value=100), minutes=st.integers(min_value=0, max_value=200), seconds=st.integers(min_value=1, max_value=200))
	def test_should_extract_correct_time_relative(self, now, hours, minutes, seconds):
		action_time = time.ActionTime()
		query = ""
		if hours: query += f"{hours} hours"
		if minutes: query += f" {minutes} minutes"
		query += f" {seconds} seconds"
		query = query.strip()
		query = f"set a timer for {query}"

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertEqual(target_time, now + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds))

	@given(now=st.datetimes(), hours=st.integers(min_value=0, max_value=100), minutes=st.integers(min_value=0, max_value=200), seconds=st.integers(min_value=1, max_value=200))
	def test_property_alarm_time_should_always_be_in_future(self, now, hours, minutes, seconds):
		action_time = time.ActionTime()
		query = ""
		if hours: query += f"{hours} hours"
		if minutes: query += f" {minutes} minutes"
		query += f" {seconds} seconds"
		query = query.strip()
		query = f"set a timer for {query}"

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertGreaterEqual(target_time, now)

if __name__ == '__main__':
	unittest.main()
