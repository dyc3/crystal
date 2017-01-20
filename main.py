#!.env/bin/python3
import numpy
import spacy
from sklearn.metrics import accuracy_score
import classifier
from datautil import DataUtil
# from speech.base import BaseSpeechRecognizer
from speech.watson import WatsonSpeechRecognizer
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
recognizer = WatsonSpeechRecognizer(config["watson_username"], config["watson_password"])
# recognizer = SphinxSpeechRecognizer()

current_utterance = None

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training...")
cmdClassifier.fit(train, labelsTrain)

micIn = audio.MicrophoneInput(dynamic_power_threshold=True)
def consoleVisualizer(frame, rate, width):
	rms = audioop.rms(frame, width)
	info = "power: " + str(rms).rjust(6)
	info += "  |  threshold: " + ("\033[32m" if rms > micIn.powerThreshold else "\033[31m") + str(micIn.powerThreshold).rjust(6) + "\033[0m"
	info += "  |  " + ("\033[32m" if recognizer.status == "speaking" else "\033[31m") + recognizer.status.rjust(12) + "\033[0m"
	info += "  |  " + "recognizer is running" if recognizer.isRunning else "recognizer is not running"
	if recognizer.isRunning:
		if recognizer.websocket_connector != None:
			# info += "  |  websocket: "+ str(recognizer.websocket) +" == " + str(dir(recognizer.websocket))
			pass
		info += "  |  (no speak: " + str(recognizer._notSpeakingTicks).rjust(4) + ")"
	info += "  |  Processing: " + str(current_utterance)
	print(info, end='\r')

def sendToRecognizer(frame, rate, width):
	# print(recognizer.websocket.__dict__)
	if recognizer.isRunning:
		recognizer.GiveFrame(frame, rate, micIn.sample_width, micIn.powerThreshold)

def onSpeech(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text

def onFinish(text):
	global current_utterance
	print("User said:", text)
	current_utterance = None
	# TODO: process text

micIn.onFrame += consoleVisualizer
micIn.onFrame += sendToRecognizer
print("Calibrating...")
micIn.Calibrate()

# start recognizer
recognizer.onSpeech += onSpeech
recognizer.onFinish += onFinish
try:
	recognizer.Start()
except Exception as e:
	print("ERROR: failed to start recognizer:",e)

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
