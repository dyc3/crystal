#!.env/bin/python3
import numpy
import spacy
from sklearn.metrics import accuracy_score
import classifier

print("Loading...")
nlp = spacy.load('en')
cmdClassifier = classifier.CommandClassifier(nlp)

train = ["what time is it", "what is today's date", "what's the time", "what time is it in eastern standard time",
		"is today friday", "give me the date", "what day of the week is it", "what time is it on the west coast",
		"is tomorrow monday", "what year is it", "what's the date", "is today tuesday", "is today wednesday",
		"what day of the month is it", "what month is it", "what's the current military time", "is it still morning",
		"pause the video", "play media", "resume playback", "suspend playback", "stop the video", "play video",
		"stop playback", "stop playing music", "set volume to 100%"]
labelsTrain = ["time", "date", "time", "time", "date", "date", "date", "time", "date", "date", "date", "date", "date",
		"date", "date", "time", "time", "media-pause", "media-play", "media-play", "media-pause", "media-pause", "media-play",
		"media-pause", "media-pause", "volume-set"]

test = ["give me the time", "is today monday", "give me the date", "what time is it on the east coast in military time",
		"what time is it in pacific standard time", "pause music", "play the video", "stop playing that"]
labelsTest = ["time", "date", "date", "time", "time", "media-pause", "media-play", "media-pause"]

print("Training...")
cmdClassifier.fit(train, labelsTrain)

print("Testing...")
preds = cmdClassifier.predict(test)

print("----------------------------------------------------------------------------------------------")
print("results:")
for (sample, pred) in zip(test, preds):
	print(sample, ":", pred)
print("accuracy:", accuracy_score(labelsTest, preds))
