from crystal.actions import BaseAction
from crystal import feedback
import subprocess, os, rofi, shlex, sys

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

def confirmAction(action):
	promptText = 'Please confim a potentially dangerous action: {}'.format(action)
	options = ['Confirm', 'Cancel']
	# if enableRofiPrompts:
	response = rofi.select(promptText, options, select=1)
	print('confirmAction: {}'.format(response))
	return response[0] == 0 and response[1] == 0
	# else:
		# confirm = pyautogui.confirm(promptText, buttons=options)
		# print('confirmAction: {}'.format(confirm))
		# return confirm == options[0]

class ActionRunProgram(BaseAction):
	"""docstring for ActionRunProgram."""
	def __init__(self):
		super(ActionRunProgram, self).__init__()
		self.handled_classifier = "run-program"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)

		if sentence.root.pos_ == "VERB" and str(sentence.root) in ["open", "run", "start", "give"]:
			for token in sentence.root.children:
				if token.dep_ == "dobj":
					program = str(token).lower()
					safe = False
					if program in ["terminal", "shell", "console", "prompt"]:
						program = "x-terminal-emulator" # TODO: make this configurable
						safe = True
					elif program in ["file browser", "file explorer", "nautilus"]:
						program = "nautilus" # TODO: make this configurable
						safe = True
					elif program in ["launcher", "rofi", "dmenu", "rafi"]:
						program = "rofi" # TODO: make this configurable
						safe = True
					elif program in ["calculator"]:
						program = "gnome-calculator"
						safe = True
					elif program in ["calendar"]:
						program = "gnome-calendar"
						safe = True
					elif program.lower() in ["youtube", "twitch", "google", "twitter", "reddit", "github"]:
						# note: twitch.com redirects to twitch.tv
						site = program.lower() + (".com" if program.lower() != "twitch" else ".tv")
						program = "{} {}".format("firefox", site) # TODO: make this configurable
						safe = True
					else:
						safe = False
						package_list = './getpackages-deb.sh'
						program = str(token).lower()
						for package in run_command_output(package_list):
							if program in str(package):
								program = package.decode('ascii').rstrip('\n')
								break
						print("GUESS: execute {0}".format(program))
					try:
						if program == "nautilus":
							program = "nautilus --no-desktop"
						elif program == "rofi":
							program = "rofi -show run"
						elif program in ["pavucontrol"]:
							safe = True
						if safe or confirmAction('run-program {}'.format(program)):
							runFork(program, shell=(not (program.startswith("chromium-browser") or program.startswith("x-www-browser"))))
						else:
							print("Action canceled upon user's request.")
					except Exception as e:
						print(e)
					break

def getAction():
	return ActionRunProgram()