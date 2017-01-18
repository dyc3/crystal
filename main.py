#!.env/bin/python3
import numpy
import spacy
from sklearn.metrics import accuracy_score
import classifier
from datautil import DataUtil
from speech.base import BaseSpeechRecognizer
import audio
import audioop
import time

print("Loading...")
nlp = spacy.load('en')
cmdClassifier = classifier.CommandClassifier(nlp)
recognizer = BaseSpeechRecognizer() # placeholder

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training...")
cmdClassifier.fit(train, labelsTrain)

# testing to see if MicrophoneInput works
micIn = audio.MicrophoneInput()
def consoleVisualizer(frame, width):
	avg = audioop.avg(frame, width)
	_max = audioop.max(frame, width)
	print("avg:",avg,"max:",_max, end='\r')
micIn.onFrame += consoleVisualizer
print("Listening...")
micIn.Start()
while micIn.isRunning:
	time.sleep(0.25)

test = ["give me the time", "is today monday", "give me the date", "what time is it on the east coast in military time",
		"what time is it in pacific standard time", "pause music", "play the video", "stop playing that"]
labelsTest = ["time", "date", "date", "time", "time", "media-pause", "media-play", "media-pause"]

print("Testing...")
preds = cmdClassifier.predict(test)

print("----------------------------------------------------------------------------------------------")
print("results:")
for (sample, pred) in zip(test, preds):
	print(sample, ":", pred)
print("accuracy:", accuracy_score(labelsTest, preds))
