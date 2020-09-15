import unittest
import datetime
import spacy
from spacy import displacy
from crystal.actions import smart_home
import crystal.core.processing

nlp = None

class TestActionSmartHome(unittest.TestCase):
	"""docstring for TestActionSmartHome."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_md")
		crystal.core.processing.nlp = nlp

	def test_get_query_type(self):
		# query, expected query type
		test_set = [
			("turn on the lamp", "interact"),
			("toggle the light", "interact"),
			("lamp on", "interact"),
			("scan for devices", "scan"),
			("look for new devices", "scan"),
			("are the lights on", "query"),
			("how many devices have you found", "query"),
			("how many devices are available", "query"),
			("how many devices are available", "query"),
			("is the lamp supposed to be on", "query"),
			("did I leave the lights on", "query"),
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
			("turn on carson's light", "carson light", 1),
			("lamp on", "lamp", 1),
		]
		action_smart_home = smart_home.ActionSmartHome()
		for query, expected_device_name, expected_objective_state in test_set:
			with self.subTest(query):
				doc = nlp(query)
				device_name, objective_state = action_smart_home.parse_interact(doc)
				self.assertEqual(device_name, expected_device_name)
				self.assertEqual(objective_state, expected_objective_state)

	def test_select_correct_device(self):
		action_smart_home = smart_home.ActionSmartHome()
		fake_devices = [
			smart_home.DeviceWrapper({"name": "Carsons Lamp"}),
			smart_home.DeviceWrapper({"name": "Carsons Room Light"}),
			smart_home.DeviceWrapper({"name": "Pauls Room Light"}),
		]
		action_smart_home.devices = fake_devices
		test_set = [
			("carson lamp", "Carsons Lamp"),
			("carsons lamp", "Carsons Lamp"),
			("lamp", "Carsons Lamp"),
			("light", "Carsons Room Light"),
			("pauls light", "Pauls Room Light"),
			("room light", "Carsons Room Light"),
			("paul room light", "Pauls Room Light"),
		]
		for device_name_input, expected_device_name in test_set:
			with self.subTest(f"{device_name_input} -> {expected_device_name}"):
				device = action_smart_home.select_device(device_name_input)
				self.assertIsNotNone(device)
				self.assertEqual(device.name, expected_device_name)

if __name__ == '__main__':
	unittest.main()
