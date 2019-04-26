import unittest
from crystal import feedback
import crystal.core.events

class TestEventRegistration(unittest.TestCase):
	"""docstring for TestEventRegistration."""

	def setUp(self):
		for a in crystal.core.events.__dir__():
			attr = getattr(crystal.core.events, a)
			if isinstance(attr, crystal.core.events.EventHook):
				attr._EventHook__handlers = []

	def test_ensure_feedback_unregister(self):
		"""
		Ensures all feedback modules unregister with events when unregister is called.
		"""
		feedback_modules = feedback.load_feedback()
		for f in feedback_modules:
			f.unregister()
		# ensure we loop through all the events
		for a in crystal.core.events.__dir__():
			attr = getattr(crystal.core.events, a)
			if isinstance(attr, crystal.core.events.EventHook):
				with self.subTest("Checking registered events for {}".format(a)):
					self.assertEqual(len(attr._EventHook__handlers), 0)

if __name__ == '__main__':
	unittest.main()
