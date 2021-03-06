import unittest
import datetime
import spacy
from crystal.actions import todo

nlp = None

class TestActionTodo(unittest.TestCase):
	"""docstring for TestActionTodo."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_parse(self):
		# query, expected result
		test_set = [
			("what's on my to-do list", "list"),
			("read my to-do list", "list"),
			("get my to-do list", "list"),
			("show me my to-do list", "list"),
			("what do i have to do today", "list"),
			("add clean board to my todo list", "add"),
		]
		action = todo.getAction()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
