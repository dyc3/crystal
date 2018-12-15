import unittest
import datetime
import spacy
from crystal.actions import manipulate_wm

nlp = None

class TestActionManipulateWm(unittest.TestCase):
	"""docstring for TestActionManipulateWm."""

	def setUp(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
		# query, expected result
		test_set = [
			("show me desktop 5", 'i3-msg "workspace 5"'),
			("switch to workspace 4", 'i3-msg "workspace 4"'),
			("pull up desktop 4", 'i3-msg "workspace 4"'),
			("go to desktop 2", 'i3-msg "workspace 2"'),
			("switch to workspace 2", 'i3-msg "workspace 2"'),

			("put this on workspace 2", 'i3-msg "move container to workspace number 2"'),
			("move this to desktop 5", 'i3-msg "move container to workspace number 5"'),

			("close this", 'i3-msg "kill"'),
			("kill this application", 'i3-msg "kill"'),
			("quit this program", 'i3-msg "kill"'),

			("toggle fullscreen", 'i3-msg "fullscreen toggle"'),
			("toggle floating", 'i3-msg "floating toggle"'),
		]
		action = manipulate_wm.ActionManipulateWm()
		for test, expectedResult in test_set:
			doc = nlp(test)
			sent = next(doc.sents)
			self.assertEqual(action.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
