import unittest
import spacy
from crystal.actions import roll_die

nlp = None

class TestActionRollDie(unittest.TestCase):
	"""docstring for TestActionRollDie."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_roll_die(self):
		result = roll_die.rollDie(6)
		assert isinstance(result, list)
		assert len(result) == 1
		assert result[0] >= 1 and result[0] <= 6

	def test_parse(self):
		# query, expected sides, expected count
		test_set = [
			("roll a die", 6, 1),
			("roll 2 dice", 6, 2),
			("roll a d6", 6, 1),
			("roll a D6", 6, 1),
			("roll 1 d6", 6, 1),
			("roll 2 d6", 6, 2),
			("roll 2d6", 6, 2),
			("roll two d6", 6, 2),
			("roll three d8", 8, 3),
			("crystal roll 1 d6", 6, 1),
			("crystal roll 2 D6", 6, 2),
			("crystal roll 5 D12", 12, 5),
			("roll 2d8", 8, 2),
			("roll 10d5", 5, 10),
			("roll four d6", 6, 4),

			("flip a coin", 2, 1),
			("flip 2 coins", 2, 2),
			("flip two coins", 2, 2),
		]
		action_roll_die = roll_die.ActionRollDie()
		for query, expected_sides, expected_count in test_set:
			with self.subTest():
				doc = nlp(query)
				# sent = next(doc.sents)
				sides, count = action_roll_die.parse(doc)

				self.assertEqual(sides, expected_sides, "Sides don't match, {}".format(query))
				self.assertEqual(count, expected_count, "Count don't match, {}".format(query))

if __name__ == '__main__':
	unittest.main()
