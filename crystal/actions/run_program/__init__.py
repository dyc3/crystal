from crystal.actions import BaseAction
from crystal.actions.responses import *
import subprocess, os, rofi, shlex, sys
import logging
log = logging.getLogger(__name__)

def run_command_output(command):
	p = subprocess.Popen(shlex.split(command),
						 stdout=subprocess.PIPE,
						 stderr=subprocess.STDOUT)
	return iter(p.stdout.readline, b'')

def runFork(command, shell=True):
	print("Fork running {}...".format(command))
	kwargs = {}
	if sys.version_info < (3, 2):  # assume posix
		kwargs.update(preexec_fn=os.setsid)
	else:  # Python 3.2+ and Unix
		kwargs.update(start_new_session=True)
	subprocess.Popen(shlex.split(command),
					stdin=subprocess.DEVNULL,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					shell=shell, **kwargs)

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
			if any([w in ["web", "firefox", "chrome"] for w in word_strs]):
				return "web browser"
			if any([w in ["launcher", "rofi", "dmenu"] for w in word_strs]):
				return "launcher"
			if any([w in ["mail", "email", "inbox"] for w in word_strs]):
				return "mail"
			if any([w in ["calculator", "calendar"] for w in word_strs]):
				return word_strs[0]
			if any([w in ["youtube", "reddit", "twitch", "amazon", "google", "netflix"] for w in word_strs]):
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
		if program_type in ["calculator", "calendar"]:
			return "gnome-{}".format(program_type)
		if program_type in ["youtube", "reddit", "twitch", "amazon", "google", "netflix"]:
			if program_type == "twitch":
				suffix = ".tv"
			else:
				suffix = ".com"
			return "x-www-browser {}{}".format(program_type, suffix)

	@classmethod
	def run(self, doc):
		program_type = self.parse(doc)
		log.debug("program_type = {}".format(program_type))
		if not program_type:
			return ActionResponseBasic(ActionResponseType.FAILURE, "Unable to determine program_type")
		program = self.determine_program(program_type)
		log.debug("program = {}".format(program))
		if not program:
			return ActionResponseBasic(ActionResponseType.FAILURE, "Unable to determine exact program from program type: {}".format(program_type))
		log.info("Running command: {}".format(program))

		# We need to spawn these processes without crystal's virtualenv, and reset the working directory
		command = "/bin/bash -c 'unset VIRTUAL_ENV; cd; {}'".format(program)
		log.debug("Full command: {}".format(command))
		subprocess.Popen(shlex.split(command),
						stdin=subprocess.DEVNULL,
						stdout=subprocess.DEVNULL,
						stderr=subprocess.DEVNULL,
						)
		return ActionResponseQuery("Running {}".format(program))

def getAction():
	return ActionRunProgram()