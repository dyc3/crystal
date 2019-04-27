import unittest
import datetime
import spacy
from crystal.actions import run_program

nlp = None

class TestActionRunProgram(unittest.TestCase):
	"""docstring for TestActionRunProgram."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
		# query, expected result
		test_set = [
			("give me a terminal", "terminal"),
			("give me a shell", "terminal"),
			("open a new terminal", "terminal"),
			("open up a console", "terminal"),
			("give me a prompt", "terminal"),

			("show me the program launcher", "launcher"),
			("open dmenu", "launcher"),
			("open rofi", "launcher"),

			("open a file browser", "file browser"),
			("open nautilus", "file browser"),
			("open my files", "file browser"),

			("open a web browser", "web browser"),
			("open firefox", "web browser"),
			("open chrome", "web browser"),

			("open calendar", "calendar"),
			("open up the calculator", "calculator"),
		]
		action = run_program.getAction()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				self.assertEqual(action.parse(doc), expectedResult, test)

	def test_determine_program(self):
		test_set = [
			("terminal", "x-terminal-emulator"),
			("web browser", "x-www-browser"),
			("file browser", "nautilus --no-desktop"),
			("launcher", "rofi -show run"),
			("calendar", "gnome-calendar"),
			("calculator", "gnome-calculator"),
		]
		action = run_program.getAction()
		for test, expectedResult in test_set:
			with self.subTest():
				self.assertEqual(action.determine_program(test), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
