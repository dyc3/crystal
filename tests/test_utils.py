import unittest
import spacy
import utils

nlp = None

class TestUtils(unittest.TestCase):
	"""docstring for TestUtils."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_find_word(self):
		# should find word
		doc = nlp("Hello, world!")
		token = utils.find_word(doc, ["hello"])
		self.assertIsNotNone(token)
		self.assertEqual(token.lemma_, "hello")
		token = utils.find_word(doc, "hello")
		self.assertIsNotNone(token)
		self.assertEqual(token.lemma_, "hello")

		# should find first word if there are duplicates
		doc = nlp("The quick brown fox jumps over the lazy dog.")
		token = utils.find_word(doc, ["the"])
		self.assertIsNotNone(token)
		self.assertEqual(token.lemma_, "the")
		self.assertEqual(token.i, 0)

		# should find the first word given more than one word
		token = utils.find_word(doc, ["dog", "fox"])
		self.assertIsNotNone(token)
		self.assertEqual(token.lemma_, "fox")


if __name__ == '__main__':
	unittest.main()