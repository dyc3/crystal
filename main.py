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
import logging, coloredlogs
from crystal import actions, feedback, core
from crystal.actions.responses import *
import crystal.input.speech_recognition_input

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="voice", const='voice', nargs='?', choices=["voice", "text"], required=False)
parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Set logger log level (default: INFO).")
parser.add_argument("--verbose", action='store_true', help="Increase verbosity (within confines of provided log level).")

args = parser.parse_args()

# set up log levels
coloredlogs.install(level=args.log_level)
if args.verbose:
	logging.getLogger("blink1.blink1").setLevel(logging.DEBUG)
else:
	logging.getLogger("blink1.blink1").setLevel(logging.INFO)

log.debug(args)
log.info("Mode: {}".format(args.mode))

log.info("Loading...")
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
log.info("{} action modules loaded".format(len(commands)))
log.debug(commands)
feedback_modules = feedback.load_feedback()
log.info("{} feedback modules loaded".format(len(feedback_modules)))
log.debug(feedback_modules)

current_utterance = None

train, labelsTrain = DataUtil.loadTrainingData("training.txt")
log.info("Training command classifier...")
cmdClassifier.fit(train, labelsTrain)

def on_utterance_update(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text
	core.set_status(core.CrystalStatus.LISTENING)

def on_utterance_finish(text):
	global current_utterance
	log.info("User said: {}".format(text))
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = nlp(text)
	if isSpeakingToCrystal(doc) or args.mode == "text":
		core.set_status(core.CrystalStatus.BUSY)
		try:
			classification = cmdClassifier.predict([text])[0]
			log.info("Action detected: {}".format(classification))
			action_result = commands[classification].run(doc)
			if not action_result:
				# TODO: create a more robust response system, so that
				# crystal can display complex information, ask for more missing parameters, etc.
				# (this is in progress)
				log.warn("Action did not return result. All actions must return result.")
			elif not isinstance(action_result, ActionResponseBase):
				log.warn("Action returned a {}, responses should be derived from ActionResponseBase.".format(type(action_result)))
			try:
				crystal.core.on_action_finish.fire(action_result)
			except Exception as e:
				log.error("error occured in on_action_finish")
				log.exception(e)
				traceback.print_exc()
		except Exception as e:
			log.exception(e)
			traceback.print_exc()
			crystal.core.on_action_error.fire()
	else:
		log.debug("user not talking to me")
	core.set_status(core.CrystalStatus.IDLE)

def on_action_error():
	"""
	Run when an error occurs while running an action.
	"""
	core.set_status(core.CrystalStatus.ERROR)

def on_action_finish(result):
	log.info("Action result: {} {}".format(result.type, result))

	if isinstance(result, ActionResponseBase):
		if result.type == ActionResponseType.SUCCESS:
			if isinstance(result, ActionResponseQuery):
				feedback.ShowNotify(result.message)
			elif isinstance(result, ActionResponsePromptList):
				# TODO: replace this with a rofi prompt
				list_text = "List Result:\n"
				for i in result.items:
					list_text += "* " + str(i) + "\n"
				feedback.ShowNotify(list_text)
				crystal.actions.responses.show_user_prompt(result)
		elif result.type == ActionResponseType.FAILURE:
			feedback.ShowNotify("Action failed: {}".format(result.message))
		else:
			log.error("Unknown result type: {}".format(result.type))

def isSpeakingToCrystal(doc):
	sent = next(doc.sents)
	if str(sent[0]).lower() == "crystal":
		return True
	for token in sent:
		log.debug("{} {} {} parent: {} entity: {}".format(token, token.pos_, token.dep_, token.head, token.ent_type_))
		if token.dep_ in ["npadvmod", "ccomp", "nsubj", "dobj", "ROOT"] and token.pos_ in ["NNP", "NN", "PROPN", "NOUN"] and str(token).lower() == "crystal":
			return True
	return False

def reload_commands():
	global commands, feedback_modules
	commands = actions.load_actions()
	log.info(commands)

	for f in feedback_modules:
		f.unregister()
	feedback_modules = feedback.load_feedback()
	log.info(feedback_modules)
	train, labelsTrain = DataUtil.loadTrainingData("training.txt")
	cmdClassifier.fit(train, labelsTrain)

def quit():
	log.info("Quitting...")
	user_input.StopListening()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGINT, signal_handler)
crystal.core.on_action_error += on_action_error
crystal.core.on_action_finish += on_action_finish
crystal.core.on_utterance_update += on_utterance_update
crystal.core.on_utterance_finish += on_utterance_finish

if args.mode == "voice":
	# start recognizer
	try:
		user_input.StartListening()
	except Exception as e:
		log.critical("failed to start recognizer")
		log.exception(e)

	log.info("Listening...")
	# micIn.Start()
	core.set_status(core.CrystalStatus.IDLE)
	while True:
		time.sleep(0.1)
elif args.mode == "text":
	while True:
		text_input = input("> ")
		if text_input == "":
			continue
		if text_input == "/quit":
			break
		if text_input == "/reload":
			reload_commands()
			continue
		crystal.core.on_utterance_finish.fire(text_input)
	quit()
