import unittest
import datetime
import spacy
from spacy import displacy
from crystal.actions import smart_home

nlp = None

class TestActionSmartHome(unittest.TestCase):
	"""docstring for TestActionSmartHome."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_get_query_type(self):
		# query, expected query type
		test_set = [
			("turn on the lamp", "interact"),
			("toggle the light", "interact"),
			("scan for devices", "scan"),
			("look for new devices", "scan"),
		]
		action_smart_home = smart_home.ActionSmartHome()
		for query, expected_query_type in test_set:
			with self.subTest("Testing \"{}\", expecting {}".format(query, expected_query_type)):
				doc = nlp(query)
				self.assertEqual(action_smart_home.get_query_type(doc), expected_query_type, "Query type did not match, {}".format(query))

	def test_parse_interact(self):
		# query, expected result
		test_set = [
			("turn on the lamp", "lamp", 1),
			("turn on the fucking lamp", "lamp", 1),
			("turn on the stupid light", "light", 1),
			("turn off the light", "light", 0),
			("toggle the light", "light", "toggle"),
			("toggle carson's room light", "carson room light", "toggle"),
			("toggle carson room light", "carson room light", "toggle"),
			("turn off carson's lamp", "carson lamp", 0),
			("turn on carson's light", "carson lamp", 0),
		]
		action_smart_home = smart_home.ActionSmartHome()
		for query, expected_device_name, expected_objective_state in test_set:
			with self.subTest(query):
				doc = nlp(query)
				device_name, objective_state = action_smart_home.parse_interact(doc)
				self.assertEqual(device_name, expected_device_name)
				self.assertEqual(objective_state, expected_objective_state)

if __name__ == '__main__':
	unittest.main()
