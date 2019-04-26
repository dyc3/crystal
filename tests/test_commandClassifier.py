import unittest
import numpy
import spacy
from sklearn.metrics import accuracy_score
import crystal.core.processing

class TestCommandClassifier(unittest.TestCase):

	def test_loadTraining(self):
		# TODO
		pass

	def test_commandClassifier(self):
		crystal.core.processing.load_nlp("en")
		cmdClassifier = crystal.core.processing.CommandClassifier()

		train = ["what time is it", "what is today's date", "what's the time", "what time is it in eastern standard time",
				"is today friday", "give me the date", "what day of the week is it", "what time is it on the west coast",
				"is tomorrow monday", "what year is it", "what's the date", "is today tuesday", "is today wednesday",
				"what day of the month is it", "what month is it", "what's the current military time", "is it still morning",
				"pause the video", "play media", "resume playback", "suspend playback", "stop the video", "play video",
				"stop playback", "stop playing music", "set volume to 100%", "increase volume by 15", "turn it down"]
		labelsTrain = ["time", "date", "time", "time", "date", "date", "date", "time", "date", "date", "date", "date", "date",
				"date", "date", "time", "time", "media-pause", "media-play", "media-play", "media-pause", "media-pause", "media-play",
				"media-pause", "media-pause", "volume-set", "volume-set", "volume-set"]

		test = ["give me the time", "is today monday", "give me the date", "what time is it on the east coast in military time",
				"what time is it in pacific standard time", "pause music", "play the video", "stop playing that"]
		labelsTest = ["time", "date", "date", "time", "time", "media-pause", "media-play", "media-pause"]

		cmdClassifier.fit(train, labelsTrain)
		preds = cmdClassifier.predict(test)
		accuracy = accuracy_score(labelsTest, [p[0] for p in preds])
		self.assertGreaterEqual(accuracy, 1.0)


if __name__ == '__main__':
	unittest.main()
