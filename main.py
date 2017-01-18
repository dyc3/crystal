#!.env/bin/python3
import numpy
import spacy
from sklearn.metrics import accuracy_score
import classifier
from datautil import DataUtil
# from speech.base import BaseSpeechRecognizer
from speech.watson import WatsonSpeechRecognizer
import audio
import audioop
import time
import signal
import sys

print("Loading...")
config = {}
with open("config.txt", "r") as f:
	for line in f:
		spl = line.split("=")
		config[spl[0]] = spl[1]

nlp = spacy.load('en')
cmdClassifier = classifier.CommandClassifier(nlp)
# recognizer = BaseSpeechRecognizer() # placeholder
recognizer = WatsonSpeechRecognizer(config["watson_username"], config["watson_password"])

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

def quit():
	print("Quitting...")
	recognizer.Stop()
	micIn.Stop()
	sys.exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGTERM, signal_handler)

while micIn.isRunning:
	time.sleep(0.25)
