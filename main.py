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
	rms = audioop.rms(frame, width)
	avg = audioop.avg(frame, width)
	_max = audioop.max(frame, width)
	info = str(rms).rjust(6)+"/"+str(avg).rjust(6)+"/"+str(_max).rjust(6)
	print("rms/avg/max: ", info, end='\r')
micIn.onFrame += consoleVisualizer
print("Listening...")
micIn.Start()
while micIn.isRunning:
	time.sleep(0.25)
