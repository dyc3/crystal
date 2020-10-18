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

	def test_parse_duration_to_seconds(self):
		# query, seconds
		test_set = [
			("1 second", 1),
			("10 seconds", 10),
			("100 seconds", 100),
			("1 minute and 10 seconds", 70),
			("1 minute 10 seconds", 70),
			("a twenty three minute", 23*60),
		]
		for query, expected_seconds in test_set:
			with self.subTest(query):
				doc = nlp(query)
				self.assertEqual(utils.parse_duration_to_seconds(doc), expected_seconds)

	def test_ordinal_to_int(self):
		self.assertEqual(utils.ordinal_to_int("4th"), 4)
		self.assertEqual(utils.ordinal_to_int("fourth"), 4)
		self.assertEqual(utils.ordinal_to_int("first"), 1)
		self.assertEqual(utils.ordinal_to_int("1st"), 1)
		self.assertEqual(utils.ordinal_to_int("second"), 2)
		self.assertEqual(utils.ordinal_to_int("third"), 3)

	def test_select_number_bleedy(self):
		doc = nlp("Order twenty three grape peelers.")
		self.assertEqual(utils.select_number_bleedy(doc[1]).text, "twenty three")
		self.assertEqual(utils.select_number_bleedy(doc[2]).text, "twenty three")

		doc = nlp("Seek and destroy one hundred and sixty five testicles.")
		self.assertEqual(utils.select_number_bleedy(doc[3]).text, "one hundred and sixty five")
		self.assertEqual(utils.select_number_bleedy(doc[4]).text, "one hundred and sixty five")
		self.assertEqual(utils.select_number_bleedy(doc[5]).text, "one hundred and sixty five")
		self.assertEqual(utils.select_number_bleedy(doc[6]).text, "one hundred and sixty five")
		self.assertEqual(utils.select_number_bleedy(doc[7]).text, "one hundred and sixty five")

		doc = nlp("thirty two gallons of blinker fluid.")
		self.assertEqual(utils.select_number_bleedy(doc[0]).text, "thirty two")
		self.assertEqual(utils.select_number_bleedy(doc[1]).text, "thirty two")

		doc = nlp("found number thirty two")
		self.assertEqual(utils.select_number_bleedy(doc[2]).text, "thirty two")
		self.assertEqual(utils.select_number_bleedy(doc[3]).text, "thirty two")

		doc = nlp("five balls")
		self.assertEqual(utils.select_number_bleedy(doc[0]).text, "five")

if __name__ == '__main__':
	unittest.main()