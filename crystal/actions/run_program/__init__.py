from crystal.actions import BaseAction
from crystal.actions.responses import *
import subprocess, os, shlex, sys
import logging
log = logging.getLogger(__name__)

class ActionRunProgram(BaseAction):
	"""docstring for ActionRunProgram."""
	def __init__(self):
		super(ActionRunProgram, self).__init__()
		self.handled_classifier = "run-program"
		self.requires_updater = False

	@classmethod
	def parse(self, doc) -> str:
		"""
		Extracts what should be run from the given doc. This does NOT mean the exact program to be run.

		Outputs a string indicating the type of program to run. Possible outputs:
		- terminal
		- file browser
		- web browser
		- launcher
		- calculator
		- calendar
		"""
		for word in doc:
			word_strs = [word.lemma_, str(word).lower()]
			# any([w in [] for w in word_strs])
			if any([w in ["terminal", "shell", "console", "prompt", "bash"] for w in word_strs]):
				return "terminal"
			if any([w in ["nautilus", "file"] for w in word_strs]):
				return "file browser"
			if any([w in ["web", "internet"] for w in word_strs]):
				return "web browser"
			if any([w in ["launcher", "rofi", "dmenu"] for w in word_strs]):
				return "launcher"
			if any([w in ["mail", "email", "inbox"] for w in word_strs]):
				return "mail"
			if any([w in ["volume", "audio"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["control", "panel"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "volume-control"
			if any([w in ["notepad"] for w in word_strs]):
				return "text editor"
			if any([w in ["text", "note"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["editor", "edit", "pad"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "text editor"
			if any([w in ["g"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["edit"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "text editor"
			if any([w in ["calculator", "calendar"] for w in word_strs]):
				return word_strs[0]
			if any([w in ["youtube", "reddit", "twitch", "amazon", "google", "netflix", "github"] for w in word_strs]):
				return word_strs[0]
			if any([w in ["together"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["tube"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "togethertube"
			if any([w in ["dab"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["room"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "togethertube-dab"
			if any([w in ["dc"] for w in word_strs]) and word.i < len(doc) - 1 and any([w in ["universe"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
				return "dc-universe"
			if any([w in ["screeps"] for w in word_strs]):
				if word.i < len(doc) - 1 and any([w in ["documentation", "docs", "api"] for w in [word.nbor(1).lemma_, str(word.nbor(1)).lower()]]):
					return "screeps-docs"
				else:
					return "screeps"
			if any([w.endswith(".com") or w.endswith(".org") or w.endswith(".net") or w.endswith(".io") for w in word_strs]):
				return word_strs[0]

	@classmethod
	def determine_program(self, program_type: str) -> str:
		"""
		Determine the exact program to run and the exact arguments.
		"""
		if program_type == "terminal":
			return "x-terminal-emulator"
		if program_type == "file browser":
			return "nautilus --no-desktop"
		if program_type == "web browser":
			return "x-www-browser"
		if program_type == "launcher":
			return "rofi -show run"
		if program_type == "mail":
			return "x-www-browser mail.google.com"
		if program_type == "volume-control":
			return "pavucontrol"
		if program_type == "text editor":
			return "gedit"
		if program_type in ["calculator", "calendar"]:
			return "gnome-{}".format(program_type)
		if program_type in ["youtube", "reddit", "twitch", "amazon", "google", "netflix", "github"]:
			if program_type == "twitch":
				suffix = ".tv"
			else:
				suffix = ".com"
			return "x-www-browser {}{}".format(program_type, suffix)
		if program_type == "togethertube":
			return "x-www-browser opentogethertube.com"
		if program_type == "togethertube-dab":
			return "x-www-browser opentogethertube.com/room/dab"
		if program_type == "dc-universe":
			return "x-www-browser dcuniverse.com"
		if program_type == "screeps":
			return "x-www-browser https://screeps.com/a/#!/map"
		if program_type == "screeps-docs":
			return "x-www-browser https://docs.screeps.com/api/"
		if any([program_type.endswith(s) for s in [".com", ".org", ".net", ".io"]]):
			return "x-www-browser {}".format(program_type)

	@classmethod
	def run(self, doc):
		program_type = self.parse(doc)
		log.debug("program_type = {}".format(program_type))
		program = None
		if program_type:
			program = self.determine_program(program_type)
		else:
			log.warn("unable to determine program type, attempting heuristic")
			# heuristic to open arbitrary programs
			try:
				for word in doc:
					if word.lemma_ in ["open", "run"]:
						program = str(word.nbor(1)).lower()
			except IndexError:
				pass
			if not program:
				return ActionResponseBasic(ActionResponseType.FAILURE, "Unable to determine program_type, and heuristic failed")
		log.debug("program = {}".format(program))
		if not program:
			return ActionResponseBasic(ActionResponseType.FAILURE, "Unable to determine exact program from program type: {}".format(program_type))
		log.info("Running command: {}".format(program))

		# We need to spawn these processes without crystal's virtualenv, and reset the working directory
		# We also need to spawn these processes such that Crystal is not the parent process
		command = "/usr/bin/env sh -c 'unset VIRTUAL_ENV; cd; {} & disown'".format(program)
		log.debug("Full command: {}".format(command))
		subprocess.Popen(shlex.split(command),
						stdin=subprocess.DEVNULL,
						stdout=subprocess.DEVNULL,
						stderr=subprocess.DEVNULL,
						start_new_session=True)
		return ActionResponseQuery("Running {}".format(program))

def getAction():
	return ActionRunProgram()