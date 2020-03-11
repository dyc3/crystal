import unittest
import spacy
import crystal.core
from crystal.actions import language
from crystal.actions.responses import *

nlp = None

class TestActionLanguage(unittest.TestCase):
	"""docstring for TestActionLanguage."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")
		crystal.core.config = crystal.core.load_config("config.txt")

	def test_parse(self):
		# query, expected command, expected target word
		test_set = [
			("spell backflip", "spell", "backflip"),
			("spell firefly", "spell", "firefly"),
			("spell dystopia", "spell", "dystopia"),
			("how do you spell apple", "spell", "apple"),

			("define backflip", "define", "backflip"),
			("define dystopia", "define", "dystopia"),
			("define french", "define", "french"),
			("what is the definition of version", "define", "version"),
		]
		action_language = language.getAction()
		for query, expected_command, expected_target_word in test_set:
			with self.subTest():
				doc = nlp(query)
				command, target_word = action_language.parse(doc)

				self.assertEqual(command, expected_command, "Command doesn't match, {}".format(query))
				self.assertEqual(target_word, expected_target_word, "Target word doesn't match, {}".format(query))

	def test_response_spell_1(self):
		action_language = language.getAction()
		response = action_language.run(nlp("spell icup"))
		self.assertEqual(response.type, ActionResponseType.SUCCESS)
		self.assertEqual(response.message, "I C U P")

	def test_response_spell_2(self):
		action_language = language.getAction()
		response = action_language.run(nlp("how do you spell backflip"))
		self.assertEqual(response.type, ActionResponseType.SUCCESS)
		self.assertEqual(response.message, "B A C K F L I P")

if __name__ == '__main__':
	unittest.main()
