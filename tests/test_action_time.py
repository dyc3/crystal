import unittest
import spacy
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
		# query, command
		test_set = [
			("what is the time", "check"),
			("what's the time", "check"),
			("what time is it", "check"),
			("give me the time", "check"),

			("set an alarm for 9 AM", "set-alarm"),
			("set an alarm for 7", "set-alarm"),
			("create an alarm for 8", "set-alarm"),
			("set a timer for 8 minutes", "set-alarm"),
		]
		action_time = time.ActionTime()
		for test, expected_command in test_set:
			doc = nlp(test)
			result_command = action_time.parse(doc)
			self.assertEqual(result_command, expected_command)

if __name__ == '__main__':
	unittest.main()
