import unittest
from crystal.actions import roll_die

class TestActionRollDie(unittest.TestCase):
	"""docstring for TestActionRollDie."""

	def test_roll_die(self):
		result = roll_die.rollDie(6)
		assert isinstance(result, list)
		assert len(result) == 1
		assert result[0] >= 1 and result[0] <= 6

if __name__ == '__main__':
	unittest.main()
