from enum import Enum
from abc import ABCMeta
import os, sys, time, signal
import traceback
from pathlib import Path
import uuid
import hashlib
import wave
import utils

import spacy
from spacy import displacy

from crystal.core.events import *
import crystal.core.processing
from crystal.core.datautil import DataUtil

from crystal import actions, feedback
from crystal.actions.responses import *
import crystal.input.speech_recognition_input
import crystal.input.vosk_input
import crystal.core.audio

import logging
log = logging.getLogger(__name__)

class CrystalStatus(Enum):
	IDLE = 0
	LISTENING = 1
	BUSY = 2
	ERROR = 3
	SEMILISTENING = 4

status = CrystalStatus.IDLE
config = {}
current_utterance = None
previous_utterance = None
args = None
speech_audio_dir = Path("./data/speech")
speech_transcripts = speech_audio_dir / "transcripts.csv"

def set_status(s: CrystalStatus):
	global status
	if status != s:
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
			config[spl[0]] = spl[1].rstrip()
	return config

def get_config(key: str, optional: bool = False) -> str:
	"""
	key: Get the value that corresponds to this key.
	optional: Indicates whether or not this config option is necessary. Default: False.
	"""
	try:
		return config[key]
	except KeyError:
		if not optional:
			log.critical("Config does not contain value for {}".format(key))
		return None

def core_on_utterance_update(text: str):
	global current_utterance
	log.debug(f"Processing: {text}")
	current_utterance = text

def core_on_utterance_finish(text: str):
	global current_utterance, previous_utterance, cmdClassifier
	log.info("User said: {}".format(text))
	previous_utterance = text
	current_utterance = None

	text = text.replace("crystal", "Crystal")

	doc = crystal.core.processing.parse_nlp(text)
	if args.mode == "voice":
		if status == CrystalStatus.LISTENING and not is_speaking_to_crystal(doc):
			log.debug("user not talking to me")
			set_status(CrystalStatus.IDLE)
			return

	classification, confidence = cmdClassifier.predict([text])[0]
	log.info("Action detected: {}, confidence: {:.2f}%".format(classification, confidence * 100))
	confidence_threshold = get_config("action_confidence_threshold", optional=True) or .6
	if not isinstance(confidence_threshold, float):
		try:
			confidence_threshold = float(confidence_threshold)
		except ValueError:
			log.warn("Found action_confidence_threshold in config, but it wasn't a float. Using default value (.6)")
			confidence_threshold = .6

	if status == CrystalStatus.SEMILISTENING:
		confidence_threshold = min(0.85, confidence_threshold + 0.2)
		log.info("Semi-listening, adjusted confidence threshold to {}".format(confidence_threshold))

	if confidence < confidence_threshold:
		log.info("Confidence too low, must be > {}".format(confidence_threshold))
		set_status(CrystalStatus.IDLE)
		return
	set_status(CrystalStatus.BUSY)
	try:
		action_result = commands[classification].run(doc)
		if not action_result:
			log.warn("Action did not return result. All actions must return result.")
		elif not isinstance(action_result, ActionResponseBase):
			log.warn("Action returned a {}, responses should be derived from ActionResponseBase.".format(type(action_result)))
		try:
			on_action_finish.fire(action_result)
		except Exception as e:
			log.error("error occured in on_action_finish")
			log.exception(e)
			traceback.print_exc()
	except Exception as e:
		log.exception(e)
		traceback.print_exc()
		on_action_error.fire()

	set_status(CrystalStatus.SEMILISTENING)

def core_on_action_error():
	"""
	Run when an error occurs while running an action.
	"""
	set_status(CrystalStatus.ERROR)

def core_on_action_finish(result: ActionResponseBase):
	if not isinstance(result, ActionResponseBase):
		log.warn("core_on_action_finish received result not of type ActionResponseBase. got {} ({}) instead".format(type(result), result))
		return

	log.info("Action result: {} {}".format(result.type, result))

	if result.type == ActionResponseType.SUCCESS:
		if isinstance(result, ActionResponseQuery):
			feedback.ShowNotify(result.message)
		elif isinstance(result, ActionResponseQueryList):
			list_text = "List Result:\n"
			for i in result.items:
				list_text += "* " + str(i) + "\n"
			feedback.ShowNotify(list_text)
			crystal.actions.responses.show_user_prompt(result)
	elif result.type == ActionResponseType.FAILURE:
		feedback.ShowNotify("Action failed: {}".format(result.message))
	else:
		log.error("Unknown result type: {}".format(result.type))

def core_on_wakeword():
	set_status(CrystalStatus.LISTENING)
	crystal.core.on_utterance_start.fire()

def core_on_record_buffer(raw_audio: bytes, sample_rate: int, sample_width: int):
	if user_input.realtime:
		transcript = user_input.process_audio(raw_audio, sample_rate, sample_width)
		if transcript != current_utterance:
			on_utterance_update.fire(transcript)

def core_on_recording_finish(raw_audio: bytes, sample_rate: int, sample_width: int):
	if not user_input.realtime:
		with utils.ExecutionTimer(log, "Audio processing"):
			result_text = user_input.process_audio(raw_audio, sample_rate, sample_width)
	else:
		result_text = user_input.get_full_result()
	if not result_text:
		log.debug("No text recognized")
		set_status(CrystalStatus.IDLE)
		return
	crystal.core.on_utterance_update.fire(result_text)
	with utils.ExecutionTimer(log, "Utterance processing"):
		crystal.core.on_utterance_finish.fire(result_text)
	with utils.ExecutionTimer(log, "Saving audio to disk"):
		save_audio_with_transcript(raw_audio, sample_rate, sample_width, result_text)

def is_speaking_to_crystal(doc):
	sent = next(doc.sents)
	if str(sent[0]).lower() == "crystal":
		return True
	for token in sent:
		log.debug("{} {} {} parent: {} entity: {}".format(token, token.pos_, token.dep_, token.head, token.ent_type_))
		if token.dep_ in ["npadvmod", "ccomp", "nsubj", "dobj", "ROOT", "attr"] and token.pos_ in ["NNP", "NN", "PROPN", "NOUN"] and str(token).lower() == "crystal":
			return True
		if token.pos_ in ["PROPN"] and token.dep_ not in ["pobj"] and str(token).lower() == "crystal":
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
	on_core_exit.fire()
	if args.mode == "voice":
		# user_input.StopListening()
		crystal.core.audio.stop_listening()
	os._exit(0)

def signal_handler(signum, frame):
	quit()

def save_audio_with_transcript(raw_audio: bytes, sample_rate: int, sample_width: int, transcript: str):
	if not speech_audio_dir.exists():
		speech_audio_dir.mkdir(parents=True)
	if not speech_transcripts.exists():
		with speech_transcripts.open("w") as f:
			f.write("file_id,transcript\n")

	sha256 = hashlib.sha256()
	sha256.update(raw_audio)
	audio_hash = sha256.hexdigest()
	file_id = uuid.uuid5(uuid.NAMESPACE_X500, audio_hash)
	with wave.open(str(speech_audio_dir / f"{file_id}.wav"), "wb") as wave_file:
		wave_file.setnchannels(1)
		wave_file.setframerate(sample_rate)
		wave_file.setsampwidth(sample_width)
		wave_file.writeframes(raw_audio)
	with speech_transcripts.open("a") as f:
		f.write(f'{file_id},"{transcript}"\n')

signal.signal(signal.SIGINT, signal_handler)
on_wakeword += core_on_wakeword
on_record_buffer += core_on_record_buffer
on_recording_finish += core_on_recording_finish
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
	crystal.core.processing.load_nlp(get_config("spacy_model", True) or "en_core_web_sm")

	log.info("Loading modules...")
	global user_input, commands, feedback_modules
	# recognizer = BaseSpeechRecognizer() # placeholder
	# recognizer = WatsonSpeechRecognizer(core.get_config("watson_username"), core.get_config("watson_password"))
	# recognizer = SphinxSpeechRecognizer()
	config_user_input = get_config("input") or "vosk"
	if config_user_input == "sr-google":
		user_input = crystal.input.speech_recognition_input.SpeechRecognitionInput()
	elif config_user_input == "vosk":
		user_input = crystal.input.vosk_input.VoskInput()
	log.info(f"Selected input module: {type(user_input)}")
	commands = actions.load_actions()
	log.info("{} action modules loaded".format(len(commands)))
	log.debug(commands)
	feedback_modules = feedback.load_feedback()
	log.info("{} feedback modules loaded".format(len(feedback_modules)))
	log.debug(feedback_modules)

	log.info("Training command classifier...")
	global cmdClassifier
	cmdClassifier = crystal.core.processing.CommandClassifier()
	loaded = DataUtil.loadTrainingData("training.txt")
	train, labelsTrain = [], []
	for i in range(len(loaded[0])):
		if args.disable_actions and loaded[1][i] in args.disable_actions:
			continue
		train.append(loaded[0][i])
		labelsTrain.append(loaded[1][i])
	cmdClassifier.fit(train, labelsTrain)

	set_status(CrystalStatus.IDLE)
	log.info("Ready")

	# Main loop
	if args.mode == "voice":
		# start recognizer
		try:
			crystal.core.audio.start_listening()
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
					if args.verbose:
						log.debug("Running update() for {}".format(name))
					action.update()
	elif args.mode == "text":
		while True:
			text_input = input("> ").strip()
			if text_input == "":
				continue
			if text_input == "/quit":
				break
			if text_input == "/reload":
				reload_commands()
				continue
			if text_input.startswith("/debug"):
				text_spl = text_input.split()
				if len(text_spl) <= 1:
					log.error("subcommand required: depend, entity")
				subcommand = text_spl[1]
				if subcommand in ["dep", "depend"]:
					displacy.serve(crystal.core.processing.parse_nlp(previous_utterance), style="dep")
				elif subcommand in ["ent", "entity"]:
					displacy.serve(crystal.core.processing.parse_nlp(previous_utterance), style="ent")
				else:
					log.error("invalid subcommand")
				continue
			on_utterance_finish.fire(text_input)
		quit()
