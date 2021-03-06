import unittest
import spacy
from crystal.actions import sto_lore

nlp = None

class TestActionStoLore(unittest.TestCase):
	"""docstring for TestActionStoLore."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_parse(self):
		# query, expected volume, expected chapter
		test_set = [
			("volume 1 chapter 1", 1, 1),
			("volume 24 chapter 6", 24, 6),
			("star trek lower volume nineteen chapter four", 19, 4),
			("star trek lower volume twenty three chapter two", 23, 2),
		]
		action_sto_lore = sto_lore.ActionStoLore()
		for query, expected_volume, expected_chapter in test_set:
			with self.subTest():
				doc = nlp(query)
				volume, chapter = action_sto_lore.parse(doc)

				self.assertEqual(volume, expected_volume, "Volume don't match, {}".format(query))
				self.assertEqual(chapter, expected_chapter, "Chapter don't match, {}".format(query))

if __name__ == '__main__':
	unittest.main()
