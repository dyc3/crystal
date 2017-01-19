#!.env/bin/python3
import numpy
import spacy
from sklearn.metrics import accuracy_score
import classifier
from datautil import DataUtil
# from speech.base import BaseSpeechRecognizer
# from speech.watson import WatsonSpeechRecognizer
from speech.sphinx import SphinxSpeechRecognizer
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
# recognizer = WatsonSpeechRecognizer(config["watson_username"], config["watson_password"])
recognizer = SphinxSpeechRecognizer()

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training...")
cmdClassifier.fit(train, labelsTrain)

# testing to see if MicrophoneInput works
micIn = audio.MicrophoneInput(dynamic_power_threshold=True)
def consoleVisualizer(frame, width):
	rms = audioop.rms(frame, width)
	avg = audioop.avg(frame, width)
	_max = audioop.max(frame, width)
	info = str(rms).rjust(6)+"/"+str(avg).rjust(6)+"/"+str(_max).rjust(6) + \
		"  |  threshold: " + ("\033[32m" if rms > micIn.powerThreshold else "\033[31m") + str(micIn.powerThreshold).rjust(5) + "\033[0m"
	info += "  |  " + ("\033[32m" if recognizer.status == "speaking" else "\033[31m") + recognizer.status.rjust(12) + "\033[0m"
	info += " (no speak: " + str(recognizer._notSpeakingTicks).rjust(4) + ")"
	print("rms/avg/max: ", info, end='\r')

def sendToRecognizer(frame, width):
	if recognizer.isRunning:
		recognizer.GiveFrame(frame, micIn.powerThreshold)
	else:
		print("ERROR: recognizer not running ")

micIn.onFrame += consoleVisualizer
micIn.onFrame += sendToRecognizer
print("Calibrating...")
micIn.Calibrate()

# start recognizer
recognizer.Start()

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

# while micIn.isRunning:
# 	time.sleep(0.25)
