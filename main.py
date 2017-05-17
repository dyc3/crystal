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
import sys, os
import actions
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="voice", const='voice', nargs='?', choices=["voice", "text"], required=False)
args = parser.parse_args()

print("Mode: {}".format(args.mode))

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
commands = actions.load_actions()
print(commands)

current_utterance = None

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training command classifier...")
cmdClassifier.fit(train, labelsTrain)
print("Loading audio classifier...")
audio_classifier = audio.AudioClassifier.tryLoadFromFile()

micIn = audio.MicrophoneInput(dynamic_power_threshold=True)
def consoleVisualizer(frame, rate, width):
	rms = audioop.rms(frame, width)
	info = "power: " + str(rms).rjust(6)
	info += "  |  threshold: " + ("\033[32m" if rms > micIn.powerThreshold else "\033[31m") + str(micIn.powerThreshold).rjust(6) + "\033[0m"
	info += "  |  " + ("\033[32m" if recognizer.status == "speaking" else "\033[31m") + recognizer.status.rjust(12) + "\033[0m"
	info += "  |  " + "recognizer is running" if recognizer.isRunning else "recognizer is not running"
	if recognizer.isRunning:
		if recognizer.websocket:
			info += ("\033[32m connected" if recognizer.websocket.connected else "\033[31m disconnected") + "\033[0m"
		info += "  |  " + "(speak buffer: " + str(len(recognizer._speakingBuffer)).rjust(3) + ")" + "(no speak: " + str(recognizer._notSpeakingTicks).rjust(4) + ")"
	info += "  |  Processing: " + str(current_utterance)
	print(info, end='       \r')

def sendToRecognizer(frame, rate, width):
	# print(recognizer.websocket.__dict__)
	if recognizer.isRunning:
		if audio_classifier.predictSample(frame, rate) == "speech":
			recognizer.GiveFrame(frame, rate, micIn.sample_width, micIn.powerThreshold)

def onSpeech(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text

def onFinish(text):
	global current_utterance
	print("User said:", text)
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = nlp(text)
	if isSpeakingToCrystal(doc):
		classification = cmdClassifier.predict([text])[0]
		commands[classification].run(doc)
	else:
		print("user not talking to me")

def isSpeakingToCrystal(doc):
	sent = next(doc.sents)
	for token in sent:
		print(token, token.pos_, token.dep_, "parent:", token.head)
		if token.dep_ in ["npadvmod", "ccomp", "nsubj"] and token.pos_ in ["NNP", "NN", "PROPN"] and str(token).lower() == "crystal":
			return True
	return False

def quit():
	print("Quitting...")
	audio_classifier.saveToFile()
	recognizer.Stop()
	micIn.Stop()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGINT, signal_handler)

if args.mode == "voice":
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
elif args.mode == "text":
	while True:
		user_input = input("> ")
		if user_input == "/quit":
			break
		onFinish(user_input)
	quit()
