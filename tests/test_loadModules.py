import unittest
from crystal import actions, feedback

class TestLoadModules(unittest.TestCase):
	"""docstring for TestLoadModules."""

	def test_loadActions(self):
		actions.load_actions()

	def test_loadFeedback(self):
		feedback.load_feedback()

if __name__ == '__main__':
	unittest.main()
