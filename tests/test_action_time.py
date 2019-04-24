import unittest
import spacy
from crystal.actions import time

nlp = None

class TestActionTime(unittest.TestCase):
	"""docstring for TestActionTime."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_time_parse(self):
		# query, context timezone, expected timezone, expected time
		test_set = [
			("what is the time", None, None, None),
			("what's the time", None, None, None),
			("what time is it", None, None, None),
			("give me the time", None, None, None),

			# ("what is the time on the east coast", None, -5, None),
			# ("what is the time on the west coast", None, -8, None),
		]
		action_time = time.ActionTime()
		for test, expected_context_timezone, expected_timezone, expected_time in test_set:
			doc = nlp(test)
			sent = next(doc.sents)

			result_context_timezone, result_timezone, result_time = action_time.parse(sent)
			self.assertEqual(result_context_timezone, expected_context_timezone)
			self.assertEqual(result_timezone, expected_timezone)
			self.assertEqual(result_time, expected_time)

if __name__ == '__main__':
	unittest.main()
