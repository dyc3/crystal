import unittest
import datetime
import spacy
from crystal.actions import human_input

nlp = None

class TestActionHumanInput(unittest.TestCase):
	"""docstring for TestActionHumanInput."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_extract(self):
		# query, expected result
		test_set = [
			("click", "click", ("left",)),
			("right click", "click", ("right",)),
			("double click", "click", ("double",)),

			("scroll up", "scroll", ("up", 8)),
			("scroll down", "scroll", ("down", 8)),
			("scroll to the top", "scroll", ("up", 1000)),
			("scroll to the bottom", "scroll", ("down", 1000)),

			("move the mouse to the left by 300 pixels", "move", ("left", 300)),
			("move the mouse 300 pixels to the left", "move", ("left", 300)),
			("move the mouse to the left 300 pixels", "move", ("left", 300)),
			("move the mouse left 300 pixels", "move", ("left", 300)),

			("move the mouse to the left by 30 units", "move", ("left", 300)),
			("move the mouse to the left 30 units", "move", ("left", 300)),
			("move the mouse 30 units to the left", "move", ("left", 300)),
			("move the mouse left 30 units", "move", ("left", 300)),

			("move the mouse to the right by 300 pixels", "move", ("right", 300)),
			("move the mouse 300 pixels to the right", "move", ("right", 300)),

			("move the mouse 300 pixels up", "move", ("up", 300)),
			("move the mouse 300 pixels down", "move", ("down", 300)),
		]
		action = human_input.ActionHumanInput()
		for query, expected_act, expected_params in test_set:
			with self.subTest():
				doc = nlp(query)
				act, params = action.extract_parameters(doc)
				self.assertEqual(act, expected_act, "Action {} does not match expected {}, {}".format(act, expected_act, query))
				self.assertEqual(params, expected_params, "Params {} does not match expected {}, {}".format(params, expected_params, query))

	def test_type(self):
		# query, expected result
		test_set = [
			("type ligma", "type", ("ligma",)),
			("dictate ligma", "type", ("ligma",)),
			("type (", "type", ("(",)),
			("type [", "type", ("[",)),
			("type the word (", "type", ("parenthesis",)),
			("type the word )", "type", ("closed parenthesis",)),
			("type the words )", "type", ("closed parenthesis",)),
			("type 4.85", "type", ("4.85",)),
			("type 4.5 the amount of strawberries", "type", ("4.5 the amount of strawberries",)),
			("type 6 apples for $4", "type", ("6 apples for $4",)),
			("type 12 apples and 4 bananas", "type", ("12 apples and 4 bananas",)),
			("type 65.78 to 4:3", "type", ("65.78243",)),
			("type 712-8347", "type", ("7128347",)),
			("type 1 284 8.4", "type", ("12848.4",)),
			("type 7 two 8 point 7", "type", ("728.7",)),
		]
		action = human_input.ActionHumanInput()
		for query, expected_act, expected_params in test_set:
			with self.subTest(query):
				doc = nlp(query)
				act, params = action.extract_parameters(doc)
				self.assertEqual(act, expected_act, "Action {} does not match expected {}, {}".format(act, expected_act, query))
				self.assertEqual(params, expected_params, "Params {} does not match expected {}, {}".format(params, expected_params, query))

if __name__ == '__main__':
	unittest.main()
