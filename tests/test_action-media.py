import unittest
import datetime
import spacy
from crystal.actions import media

nlp = None

class TestActionMedia(unittest.TestCase):
	"""docstring for TestActionMedia."""

	def setUp(self):
		global nlp
		nlp = spacy.load("en")

	def test_date_verify(self):
		# query, expected result
		test_set = [
			("play song", "play"),
			("play the video", "play"),
			("resume playback", "play"),
			("resume media playback", "play"),

			("pause music", "pause"),
			("pause playback", "pause"),
			("pause media playback", "pause"),
			("hold playback", "pause"),

			("skip this song", "next"),
			("next song", "next"),

			("previous song", "previous"),
			("previous video", "previous"),
		]
		action_media = media.ActionMedia()
		for test, expectedResult in test_set:
			doc = nlp(test)
			sent = next(doc.sents)
			self.assertEqual(action_media.parse(sent), expectedResult)

if __name__ == '__main__':
	unittest.main()
