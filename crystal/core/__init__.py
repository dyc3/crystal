from enum import Enum
from abc import ABCMeta
import os, sys, time, signal
import traceback
from pathlib import Path

import spacy
spacy.prefer_gpu()

from eventhook import EventHook
import classifier
from datautil import DataUtil

from crystal import actions, feedback
from crystal.actions.responses import *
import crystal.input.speech_recognition_input

import logging
log = logging.getLogger(__name__)

"""
This file defines event hooks for all events throughout the pipeline, from input to output.
The event handlers are attached and defined elsewhere.
"""

on_utterance_start = EventHook("on_utterance_start")
on_utterance_update = EventHook("on_utterance_update")
on_utterance_finish = EventHook("on_utterance_finish")
on_input_error = EventHook("on_input_error")
on_action_start = EventHook("on_action_start")
on_action_finish = EventHook("on_action_finish")
on_action_error = EventHook("on_action_error")
on_status_update = EventHook("on_status_update")

class CrystalStatus(Enum):
	IDLE = 0
	LISTENING = 1
	BUSY = 2
	ERROR = 3

status = CrystalStatus.IDLE
config = {}
current_utterance = None

def set_status(s: CrystalStatus):
	global status
	status = s
	log.info("STATUS: {}".format(status))
	on_status_update.fire(status)

def load_config(path: Path) -> dict:
	"""
	Returns dict with config values from the file.
	"""
	if isinstance(path, str):
		path = Path(path)

	config = {}
	with path.open() as f:
		for line in f:
			spl = line.split("=")
			config[spl[0]] = spl[1]
	return config

def get_config(key: str) -> str:
	try:
		return config[key]
	except KeyError:
		log.critical("Config does not contain value for {}".format(key))
		return None

def load_nlp(model: str):
	"""
	model: specify spaCy model to use
	"""
	try:
		nlp = spacy.load(model)
	except OSError:
		# model loading failed, it probably doesn't exist
		# download it
		os.system("python -m spacy download {}".foramt(model))
		nlp = spacy.load(model)
	return nlp

def core_on_utterance_update(text):
	global current_utterance
	# print("Processing:", text)
	current_utterance = text
	core.set_status(core.CrystalStatus.LISTENING)

def core_on_utterance_finish(text):
	global current_utterance, nlp, cmdClassifier
	log.info("User said: {}".format(text))
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = nlp(text)
	if is_speaking_to_crystal(doc) or args.mode == "text":
		set_status(CrystalStatus.BUSY)
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
	set_status(CrystalStatus.IDLE)

def core_on_action_error():
	"""
	Run when an error occurs while running an action.
	"""
	set_status(CrystalStatus.ERROR)

def core_on_action_finish(result):
	log.info("Action result: {} {}".format(result.type, result))

	if not isinstance(result, ActionResponseBase):
		log.warn("core_on_action_finish received result not of type ActionResponseBase. got {} ({}) instead".format(type(result), result))
		return

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

def is_speaking_to_crystal(doc):
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
	if args.mode == "voice":
		user_input.StopListening()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

signal.signal(signal.SIGINT, signal_handler)
on_action_error += core_on_action_error
on_action_finish += core_on_action_finish
on_utterance_update += core_on_utterance_update
on_utterance_finish += core_on_utterance_finish

def run(in_args):
	"""
	Main loop for Crystal. Initializes and enters request/response loop.

	in_args: parsed arguments from argparse
	"""
	set_status(CrystalStatus.BUSY)
	global args
	args = in_args
	log.debug(args)
	log.info("Mode: {}".format(args.mode))

	log.info("Loading config...")
	global config
	config = load_config("config.txt")
	log.info("Config loaded, found {} items".format(len(config)))

	log.info("Loading NLP model...")
	global nlp
	nlp = load_nlp("en")

	log.info("Loading modules...")
	global user_input, commands, feedback_modules
	# recognizer = BaseSpeechRecognizer() # placeholder
	# recognizer = WatsonSpeechRecognizer(core.get_config("watson_username"), core.get_config("watson_password"))
	# recognizer = SphinxSpeechRecognizer()
	user_input = crystal.input.speech_recognition_input.SpeechRecognitionInput()
	commands = actions.load_actions()
	log.info("{} action modules loaded".format(len(commands)))
	log.debug(commands)
	feedback_modules = feedback.load_feedback()
	log.info("{} feedback modules loaded".format(len(feedback_modules)))
	log.debug(feedback_modules)

	log.info("Training command classifier...")
	global cmdClassifier
	cmdClassifier = classifier.CommandClassifier(nlp)
	train, labelsTrain = DataUtil.loadTrainingData("training.txt")
	cmdClassifier.fit(train, labelsTrain)

	set_status(CrystalStatus.IDLE)
	log.info("Ready")

	# Main loop
	if args.mode == "voice":
		# start recognizer
		try:
			user_input.StartListening()
		except Exception as e:
			log.critical("failed to start recognizer")
			log.exception(e)

		log.info("Listening...")
		# micIn.Start()
		set_status(CrystalStatus.IDLE)
		while True:
			time.sleep(1)

			# run updaters for actions
			for name, action in commands.items():
				if action.requires_updater:
					# This is useful for reminders, alarms, etc.
					# Anything that user wants Crystal do that
					# requires Crystal to do it automatically.
					log.debug("Running update() for {}".format(name))
					action.update()
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
			on_utterance_finish.fire(text_input)
		quit()
