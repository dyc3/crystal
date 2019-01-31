import unittest
import crystal.core
import crystal.core.processing
import spacy
from spacy import displacy

nlp = spacy.load('en')

class TestCoreIsTalkingToMe(unittest.TestCase):
	"""docstring for TestCoreIsTalkingToMe."""

	def test_is_talking_to_me(self):
		test_set = [
			("Crystal what day is it", True),
			("what day is it Crystal", True),

			("Crystal tell me what day it is", True),
			("tell me what day it is Crystal", True),

			("Crystal what's the date", True),
			("what's the date Crystal", True),
		]

		for query, expected_result in test_set:
			doc = nlp(query)
			result = crystal.core.is_speaking_to_crystal(doc)
			if expected_result != result:
				displacy.serve(doc)
			self.assertEqual(result, expected_result, "Results did not match. Expected: {} Got: {}, {}".format(expected_result, result, query))

if __name__ == '__main__':
	unittest.main()
