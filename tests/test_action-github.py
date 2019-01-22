import unittest
import spacy
from crystal.actions import github

nlp = None

class TestActionGithub(unittest.TestCase):
	"""docstring for TestActionGithub."""

	def setUp(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
		# query, expected sides, expected count
		test_set = [
			("how many notifications are on Github", "list-notif"),
			("how many notifications do I have on Github", "list-notif"),
			("check github notifications", "list-notif"),

			("list my repositories", "list-repos"),
			("how many repositories do I have", "list-repos"),
		]
		action_github = github.ActionGithub()
		for query, expected_command in test_set:
			doc = nlp(query)
			sent = next(doc.sents)
			command = action_github.parse(sent)

			self.assertEqual(command, expected_command, "Command doesn't match, {}".format(query))

if __name__ == '__main__':
	unittest.main()
