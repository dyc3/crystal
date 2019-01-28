import unittest
from crystal import actions, feedback

class TestLoadModules(unittest.TestCase):
	"""docstring for TestLoadModules."""

	def test_loadActions(self):
		actions.load_actions()

	def test_check_actions_for_duplicate_handlers(self):
		"""
		Checks handled_classifier in each action module for duplicates.
		"""
		action_modules = actions.load_actions()
		seen_handlers = []
		for a in action_modules:
			self.assertFalse(a in seen_handlers)
			seen_handlers.append(a)

	def test_loadFeedback(self):
		feedback.load_feedback()

if __name__ == '__main__':
	unittest.main()
