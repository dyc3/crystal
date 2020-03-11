import unittest
import datetime
import spacy
from crystal.actions import manipulate_wm

nlp = None

class TestActionManipulateWm(unittest.TestCase):
	"""docstring for TestActionManipulateWm."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_parse(self):
		# query, expected result
		test_set = [
			("show me desktop 5", 'i3-msg "workspace 5"'),
			("switch to workspace 4", 'i3-msg "workspace 4"'),
			("pull up desktop 4", 'i3-msg "workspace 4"'),
			("go to desktop 2", 'i3-msg "workspace 2"'),
			("switch to workspace 2", 'i3-msg "workspace 2"'),
			("go to desktop number 2", 'i3-msg "workspace 2"'),
			("switch to workspace one", 'i3-msg "workspace 1"'),
			("show me workspace number three", 'i3-msg "workspace 3"'),

			("put this on workspace 2", 'i3-msg "move container to workspace number 2"'),
			("move this to desktop 5", 'i3-msg "move container to workspace number 5"'),
			("put this on workspace number 3", 'i3-msg "move container to workspace number 3"'),
			("move this to workspace six", 'i3-msg "move container to workspace number 6"'),
			("move that to workspace seven", 'i3-msg "move container to workspace number 7"'),
			("put this on workspace number eight", 'i3-msg "move container to workspace number 8"'),

			("close this", 'i3-msg "kill"'),
			("kill this application", 'i3-msg "kill"'),
			("quit this program", 'i3-msg "kill"'),

			("toggle floating", 'i3-msg "floating toggle"'),
			("make this float", 'i3-msg "floating enable"'),
			("make this window float", 'i3-msg "floating enable"'),
			("enable floating", 'i3-msg "floating enable"'),
			("enable float", 'i3-msg "floating enable"'),
			("disable floating", 'i3-msg "floating disable"'),
			("disable float", 'i3-msg "floating disable"'),

			("toggle fullscreen", 'i3-msg "fullscreen toggle"'),
			("make this full screen", 'i3-msg "fullscreen enable"'),
			("make this fullscreen", 'i3-msg "fullscreen enable"'),
			("enable full screen", 'i3-msg "fullscreen enable"'),
			("enable fullscreen", 'i3-msg "fullscreen enable"'),
			("disable full screen", 'i3-msg "fullscreen disable"'),
			("disable fullscreen", 'i3-msg "fullscreen disable"'),
		]
		action = manipulate_wm.ActionManipulateWm()
		for test, expectedResult in test_set:
			with self.subTest(test):
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action.parse(sent), expectedResult, test)

	def test_parse_move_workspace_to_output(self):
		# query, expected result
		test_set = [
			("move this workspace up", 'i3-msg "move workspace to output up"'),
			("move workspace down", 'i3-msg "move workspace to output down"'),
			("move work space left", 'i3-msg "move workspace to output left"'),
			("move this desktop to the right", 'i3-msg "move workspace to output right"'),
			("move this workspace to the primary display", 'i3-msg "move workspace to output primary"'),
		]
		action = manipulate_wm.ActionManipulateWm()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
