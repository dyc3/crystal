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
import argparse
import traceback
from crystal import input, actions, feedback
import crystal.input.speech_recognition_input

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
# recognizer = WatsonSpeechRecognizer(config["watson_username"], config["watson_password"])
# recognizer = SphinxSpeechRecognizer()
user_input = crystal.input.speech_recognition_input.SpeechRecognitionInput()
commands = actions.load_actions()
print(commands)

current_utterance = None

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training command classifier...")
cmdClassifier.fit(train, labelsTrain)

def on_utterance_update(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text
	feedback.OnStatus("listening")

def on_utterance_finish(text):
	global current_utterance
	print("User said:", text)
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = nlp(text)
	if isSpeakingToCrystal(doc) or args.mode == "text":
		feedback.OnStatus("working")
		try:
			classification = cmdClassifier.predict([text])[0]
			commands[classification].run(doc)
		except Exception as e:
			feedback.OnStatus("error")
			print(e)
			traceback.print_exc()
	else:
		print("user not talking to me")
	feedback.OnStatus("idle")

def isSpeakingToCrystal(doc):
	sent = next(doc.sents)
	if str(sent[0]).lower() == "crystal":
		return True
	for token in sent:
		print(token, token.pos_, token.dep_, "parent:", token.head, "entity:", token.ent_type_)
		if token.dep_ in ["npadvmod", "ccomp", "nsubj", "dobj", "ROOT"] and token.pos_ in ["NNP", "NN", "PROPN", "NOUN"] and str(token).lower() == "crystal":
			return True
	return False

def reload_commands():
	global commands
	commands = actions.load_actions()
	print(commands)
	train, labelsTrain = DataUtil.loadTrainingData("training.txt")
	cmdClassifier.fit(train, labelsTrain)

def quit():
	print("Quitting...")
	user_input.StopListening()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGINT, signal_handler)

if args.mode == "voice":
	# start recognizer
	user_input.on_utterance_update += on_utterance_update
	user_input.on_utterance_finish += on_utterance_finish
	try:
		user_input.StartListening()
	except Exception as e:
		print("ERROR: failed to start recognizer:",e)

	print("Listening...")
	# micIn.Start()
	feedback.OnStatus("idle")
elif args.mode == "text":
	while True:
		user_input = input("> ")
		if user_input == "/quit":
			break
		elif user_input == "/reload":
			reload_commands()
			continue
		on_utterance_finish(user_input)
	quit()
