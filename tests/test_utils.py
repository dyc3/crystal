import unittest
import spacy
import utils

nlp = None

class TestUtils(unittest.TestCase):
	"""docstring for TestUtils."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

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

	# TODO: implement this utility
	# def test_parse_duration_to_seconds(self):
	# 	# query, seconds
	# 	test_set = [
	# 		("1 second", 1),
	# 		("10 seconds", 10),
	# 		("100 seconds", 100),
	# 		("1 minute and 10 seconds", 70),
	# 		("1 minute 10 seconds", 70),
	# 	]
	# 	for query, expected_seconds in test_set:
	# 		with self.subTest(query):
	# 			doc = nlp(query)
	# 			self.assertEqual(utils.parse_duration_to_seconds(doc), expected_seconds)


if __name__ == '__main__':
	unittest.main()