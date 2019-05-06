import unittest
import spacy
from crystal.actions import github

nlp = None

class TestActionGithub(unittest.TestCase):
	"""docstring for TestActionGithub."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
		# query, expected sides, expected count
		test_set = [
			("how many notifications are on Github", "count-notif"),
			("how many notifications do I have on Github", "count-notif"),
			("check github notifications", "list-notif"),
			("list github notifications", "list-notif"),
			("show me my github notifications", "list-notif"),

			("how many repositories do I have", "count-repos"),
			("list my repositories", "list-repos"),
		]
		action_github = github.ActionGithub()
		for query, expected_command in test_set:
			with self.subTest():
				doc = nlp(query)
				sent = next(doc.sents)
				command = action_github.parse(sent)

				self.assertEqual(command, expected_command, "Command doesn't match, {}".format(query))

if __name__ == '__main__':
	unittest.main()
