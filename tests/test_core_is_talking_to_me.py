import unittest
import crystal.core
import crystal.core.processing
import spacy
from spacy import displacy

nlp = spacy.load('en_core_web_sm')

class TestCoreIsTalkingToMe(unittest.TestCase):
	"""docstring for TestCoreIsTalkingToMe."""

	def test_is_talking_to_me(self):
		test_set = [
			("Crystal what day is it", True),
			("what day is it Crystal", True),
			("what day is it, Crystal?", True),

			("Crystal tell me what day it is", True),
			("tell me what day it is Crystal", True),

			("Crystal what's the date", True),
			("what's the date Crystal", True),

			("I'm talking about Crystal and she shouldn't activate", False),
			("Working on Crystal is fun", False),
			("it can we do that on my defend the crystal phone", False),
		]

		for query, expected_result in test_set:
			doc = nlp(query)
			# displacy.serve(doc, style="dep")
			result = crystal.core.is_speaking_to_crystal(doc)
			self.assertEqual(result, expected_result, "Results did not match. Expected: {} Got: {}, {}".format(expected_result, result, query))

if __name__ == '__main__':
	unittest.main()
