import unittest
import datetime
import spacy
from crystal.actions import human_input

nlp = None

class TestActionHumanInput(unittest.TestCase):
	"""docstring for TestActionHumanInput."""

	def setUp(self):
		global nlp
		nlp = spacy.load("en")

	def test_extract(self):
		# query, expected result
		test_set = [
			("move the mouse 300 pixels to the left", "move", "left 300"),
			("move the mouse 300 pixels to the right", "move", "right 300"),
		]
		action = human_input.ActionHumanInput()
		for query, expected_act, expected_params in test_set:
			doc = nlp(query)
			act, params = action.extract_parameters(doc)
			self.assertEqual(act, expected_act, "Action {} does not match expected {}, {}".format(act, expected_act, query))
			self.assertEqual(params, expected_params, "Params {} does not match expected {}, {}".format(params, expected_params, query))

if __name__ == '__main__':
	unittest.main()
