import unittest
import spacy
import datetime
from hypothesis import given, example
import hypothesis.strategies as st
import inflect

from crystal.actions import time

nlp = None
p = inflect.engine()

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
			("set a one hour timer", (time.ACTION_SET, time.TARGET_ALARM)),
		]
		action_time = time.ActionTime()
		for query, expected in test_set:
			with self.subTest(query):
				doc = nlp(query)
				result = action_time.parse(doc)
				self.assertEqual(result, expected)

	def test_compound_numbers(self):
		# query, now, expected delta
		test_set = [
			("set a forty five minute timer", datetime.datetime.now(), datetime.timedelta(minutes=45)),
			("set a timer for one hour fifty four minutes and one second", datetime.datetime(2000, 1, 1, 0, 0), datetime.timedelta(hours=1, minutes=54, seconds=1)),
			("set a timer for one hundred and seventy minutes and three seconds", datetime.datetime(2000, 1, 1, 0, 0), datetime.timedelta(minutes=170, seconds=3)),
		]
		action_time = time.ActionTime()
		for query, now, expected_delta in test_set:
			with self.subTest(f"{query}, now={now}"):
				doc = nlp(query)
				target_time = action_time.parse_target_time(doc, now=now)
				self.assertEqual(target_time, now + expected_delta)

	@given(now=st.datetimes(), hours=st.integers(min_value=0, max_value=100), minutes=st.integers(min_value=0, max_value=200), seconds=st.integers(min_value=1, max_value=200))
	def test_should_extract_correct_time_relative(self, now, hours, minutes, seconds):
		action_time = time.ActionTime()
		query = ""
		if hours: query += f"{hours} hours"
		if minutes: query += f" {minutes} minutes"
		if hours or minutes: query += " and"
		query += f" {seconds} seconds"
		query = query.strip()
		query = f"set a timer for {query}"

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertEqual(target_time, now + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds))

	@given(now=st.datetimes(), hours=st.integers(min_value=0, max_value=100), minutes=st.integers(min_value=0, max_value=200), seconds=st.integers(min_value=1, max_value=200))
	def test_should_extract_correct_time_relative_query_variation_1(self, now, hours, minutes, seconds):
		action_time = time.ActionTime()
		query = ""
		if hours: query += f"{hours} hour"
		if minutes: query += f" {minutes} minute"
		if hours or minutes: query += " and"
		query += f" {seconds} second"
		query = query.strip()
		query = f"set a {query} timer"

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertEqual(target_time, now + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds), query)

	@given(now=st.datetimes(), hours=st.integers(min_value=0, max_value=100), minutes=st.integers(min_value=0, max_value=200), seconds=st.integers(min_value=1, max_value=200))
	def test_should_extract_correct_time_relative_query_compound_numbers(self, now, hours, minutes, seconds):
		action_time = time.ActionTime()
		query = ""
		if hours: query += f"{p.number_to_words(hours)} {p.plural('hour', hours)}"
		if minutes: query += f" {p.number_to_words(minutes)} {p.plural('minute', minutes)}"
		if hours or minutes: query += " and"
		query += f" {p.number_to_words(seconds)} {p.plural('second', seconds)}"
		query = query.strip()
		# HACK: replace dashes with spaces, because realisically the query won't have dashes
		query = f"set a timer for {query}".replace("-", " ")

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertEqual(target_time, now + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds), f"{query}, {now}")

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

	@given(now=st.datetimes(), clock_hour=st.integers(min_value=1, max_value=12), am_or_pm=st.sampled_from(["", "am", "pm"]))
	def test_property_absolute_alarm_time_should_always_be_in_future(self, now, clock_hour, am_or_pm):
		action_time = time.ActionTime()
		query = f"set an alarm for {clock_hour} {am_or_pm}".strip()

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		self.assertGreaterEqual(target_time, now)

	@given(now=st.datetimes(), clock_hour=st.integers(min_value=1, max_value=12), am_or_pm=st.sampled_from(["am", "pm"]))
	def test_property_absolute_alarm_time_should_always_match_hour(self, now, clock_hour, am_or_pm):
		action_time = time.ActionTime()
		query = f"set an alarm for {clock_hour} {am_or_pm}".strip()

		doc = nlp(query)
		target_time = action_time.parse_target_time(doc, now=now)
		adjusted_clock_hour = (clock_hour + 12*(am_or_pm == "pm")) % 24
		if adjusted_clock_hour == 12 and am_or_pm == "am":
			adjusted_clock_hour = 0
		elif adjusted_clock_hour == 0 and am_or_pm == "pm":
			adjusted_clock_hour = 12
		self.assertEqual(adjusted_clock_hour, target_time.hour)

if __name__ == '__main__':
	unittest.main()
