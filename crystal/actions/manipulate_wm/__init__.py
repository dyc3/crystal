from crystal.actions import BaseAction
from crystal.actions.responses import *
import utils
import logging
log = logging.getLogger(__name__)

class ActionManipulateWm(BaseAction):
	"""docstring for ActionManipulateWm."""
	def __init__(self):
		super(ActionManipulateWm, self).__init__()
		self.handled_classifier = "manipulate-wm"
		self.requires_updater = False

	@classmethod
	def parse(self, sentence):
		"""
		Returns a i3-msg command with arguments to complete the action.
		"""
		workspace_token = utils.find_word(sentence.doc, ["workspace", "space", "desktop"])
		workspace_number = None
		if workspace_token:
			num_token = workspace_token.nbor(1)

			if num_token.lemma_ == "number":
				num_token = workspace_token.nbor(2)

			# just in case the input filtering doesn't catch these cases
			if num_token.text.lower() in ["to", "for"]:
				workspace_number = { "to": 2, "for": 4 }[num_token.text.lower()]

			try:
				workspace_number = int(num_token.text)
			except:
				try:
					workspace_number = utils.text2int(num_token.text.lower())
				except Exception as e:
					log.debug("Failed to parse workspace number: {}".format(e))

		command = None
		# switching workspaces
		if str(sentence.root) in ["switch", "focus", "show", "pull", "go"]:
			if workspace_token and workspace_number:
				command = 'i3-msg "workspace {}"'.format(workspace_number)
			else:
				# TODO: create Exception specifically for parsing failures
				raise Exception("Failed to parse input for workspace number")
		# moving windows to other workspaces
		elif str(sentence.root) in ["move", "put"]:
			if workspace_token.nbor(-1).text in ["to", "on"]:
				# This means that we are moving a window to the target workspace
				if not workspace_token or not workspace_number:
					# TODO: create Exception specifically for parsing failures
					raise Exception("Unable to parse for target workspace")
				if sentence.root.nbor(1).text in ["this", "that"]:
					command = 'i3-msg "move container to workspace number {}"'.format(workspace_number)
				else:
					raise Exception("Can't move other windows than the active window. You must specify that you want to move 'this' or 'that' window.")
			else:
				# This means that we are moving the target workspace to a different output
				direction = utils.find_word(sentence.doc, ["up", "down", "left", "right", "primary"])
				if not direction:
					raise Exception("Failed to parse which direction to move the current workspace")
				# if workspace_number:
					# NOTE: this is not yet supported by i3
					# command = 'i3-msg "move workspace {} to output {}"'.format(workspace_number, direction.text)
				command = 'i3-msg "move workspace to output {}"'.format(direction.text)
		elif sentence.root.lemma_ in ["kill", "close", "quit"]:
			command = 'i3-msg "kill"'
		else:
			word = utils.find_word(sentence.doc, "toggle")
			if word:
				if word.nbor(1).text in ["fullscreen"]:
					command = 'i3-msg "fullscreen toggle"'
				elif word.nbor(1).text in ["floating"]:
					command = 'i3-msg "floating toggle"'

		return command

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		try:
			command = self.parse(sentence)
		except Exception as e:
			return ActionResponseBasic(ActionResponseType.FAILURE, "Parsing failed: {}".format(e))

		if command != None:
			exitcode = utils.runAndPrint(command)
			log.debug("exit: {}".format(exitcode))
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		else:
			log.error("command == None")
			return ActionResponseBasic(ActionResponseType.FAILURE, "command == None")

def getAction():
	return ActionManipulateWm()
