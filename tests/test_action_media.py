import unittest
import datetime
import spacy
from crystal.actions import media

nlp = None

class TestActionMedia(unittest.TestCase):
	"""docstring for TestActionMedia."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_parse(self):
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

			("go to 8 seconds", "position 8"),
			("seek position to 2 minutes", "position 120"),
			("go to 2 minutes 30 seconds", "position 150"),
			("go to 2 minutes and 30 seconds", "position 150"),

			("skip ahead 4 seconds", "position +4"),
			("go forward 1 minute", "position +60"),

			("skip back 30 seconds", "position -30"),
			("skip back 1 minute and 30 seconds", "position -90"),
			("go back 4 seconds", "position -4"),
		]
		action_media = media.ActionMedia()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action_media.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
