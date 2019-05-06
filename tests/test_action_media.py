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
			("crystal play music", "play"),

			("pause music", "pause"),
			("pause playback", "pause"),
			("pause media playback", "pause"),
			("hold playback", "pause"),
			("crystal pause the music", "pause"),

			("skip this song", "next"),
			("next song", "next"),
			("crystal skip", "next"),

			("previous song", "previous"),
			("previous video", "previous"),
			("crystal go back to the previous song", "previous"),

			("go to 8 seconds", "position 8"),
			("seek position to 2 minutes", "position 120"),
			("go to 2 minutes 30 seconds", "position 150"),
			("go to 2 minutes and 30 seconds", "position 150"),
			("crystal go to 3 minutes and 45 seconds", "position 225"),

			("skip ahead 4 seconds", "position +4"),
			("go forward 1 minute", "position +60"),
			("crystal skip ahead 2 minutes and 10 seconds", "position +130"),

			("skip back 30 seconds", "position -30"),
			("skip back 1 minute and 30 seconds", "position -90"),
			("go back 4 seconds", "position -4"),
			("crystal go back 12 seconds", "position -12"),
		]
		action_media = media.ActionMedia()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action_media.parse(sent), expectedResult, test)

	def test_parse_shuffling(self):
		# query, expected result
		test_set = [
			("enable shuffle", "shuffle On"),
			("turn on shuffle mode", "shuffle On"),
			("shuffle the songs", "shuffle On"),
			("crystal shuffle the songs", "shuffle On"),

			("turn off shuffle mode", "shuffle Off"),
			("disable shuffle mode", "shuffle Off"),
			("disable shuffling", "shuffle Off"),
			("crystal disable shuffling", "shuffle Off"),
		]
		action_media = media.ActionMedia()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action_media.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
