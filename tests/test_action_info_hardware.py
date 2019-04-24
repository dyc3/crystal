import unittest
import spacy
from crystal.actions import info_hardware

nlp = None

class TestActionInfoHardware(unittest.TestCase):
	"""docstring for TestActionInfoHardware."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
		# current_volume, query string, expected result
		test_set = [
			("how many processors are available", "processors", []),
			("how many cpu threads do I have", "processors", ["logical"]),
			("how many physical cores are in the system", "processors", ["physical"]),

			("how much memory is available", "memory", []),

			("how much disk space is available", "disks", []),
			("how many disk mounts are available", "disks", []),
			("show me all storage disks", "disks", []),
		]
		action_info_hardware = info_hardware.ActionInfoHardware()
		for query, expected_type, expected_params in test_set:
			with self.subTest():
				doc = nlp(query)
				sent = next(doc.sents)

				result_type, result_params = action_info_hardware.parse(sent)
				self.assertEqual(result_type, expected_type, msg=query)
				self.assertEqual(len(result_params), len(expected_params), msg=query)
				self.assertCountEqual(result_params, expected_params, msg=query)

if __name__ == '__main__':
	unittest.main()
