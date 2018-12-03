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
from crystal import actions, feedback, core
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

spacy.prefer_gpu()
try:
	nlp = spacy.load('en')
except OSError:
	# model loading failed, it probably doesn't exist
	# download it
	os.system("python -m spacy download en")
	nlp = spacy.load('en')
cmdClassifier = classifier.CommandClassifier(nlp)
# recognizer = BaseSpeechRecognizer() # placeholder
# recognizer = WatsonSpeechRecognizer(config["watson_username"], config["watson_password"])
# recognizer = SphinxSpeechRecognizer()
user_input = crystal.input.speech_recognition_input.SpeechRecognitionInput()
commands = actions.load_actions()
print(commands)
feedback_modules = feedback.load_feedback()
print(feedback_modules)

current_utterance = None

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
print("Training command classifier...")
cmdClassifier.fit(train, labelsTrain)

def on_utterance_update(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text
	core.set_status(core.CrystalStatus.LISTENING)

def on_utterance_finish(text):
	global current_utterance
	print("User said:", text)
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = nlp(text)
	if isSpeakingToCrystal(doc) or args.mode == "text":
		core.set_status(core.CrystalStatus.BUSY)
		try:
			classification = cmdClassifier.predict([text])[0]
			commands[classification].run(doc)
		except Exception as e:
			print(e)
			traceback.print_exc()
			crystal.core.on_action_error.fire()
	else:
		print("user not talking to me")
	core.set_status(core.CrystalStatus.IDLE)

def on_action_error():
	"""
	Run when an error occurs while running an action.
	"""
	core.set_status(core.CrystalStatus.ERROR)

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
	global commands, feedback_modules
	commands = actions.load_actions()
	print(commands)

	for f in feedback_modules:
		f.unregister()
	feedback_modules = feedback.load_feedback()
	print(feedback_modules)
	train, labelsTrain = DataUtil.loadTrainingData("training.txt")
	cmdClassifier.fit(train, labelsTrain)

def quit():
	print("Quitting...")
	user_input.StopListening()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGINT, signal_handler)
crystal.core.on_action_error += on_action_error
crystal.core.on_utterance_update += on_utterance_update
crystal.core.on_utterance_finish += on_utterance_finish

if args.mode == "voice":
	# start recognizer
	try:
		user_input.StartListening()
	except Exception as e:
		print("ERROR: failed to start recognizer:",e)

	print("Listening...")
	# micIn.Start()
	core.set_status(core.CrystalStatus.IDLE)
	while True:
		time.sleep(0.1)
elif args.mode == "text":
	while True:
		text_input = input("> ")
		if text_input == "/quit":
			break
		elif text_input == "/reload":
			reload_commands()
			continue
		crystal.core.on_utterance_finish.fire(text_input)
	quit()
