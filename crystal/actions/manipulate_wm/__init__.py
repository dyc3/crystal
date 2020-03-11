import subprocess
import json

from crystal.actions import BaseAction
from crystal.actions.responses import *
import utils
import logging
log = logging.getLogger(__name__)

# TODO: don't rely on i3-msg to set commands, this should actually establish an IPC connection, see:
# - https://i3wm.org/docs/ipc.html#_establishing_a_connection
# - https://github.com/Ceryn/i3msg-python

# TODO: create layer of abstraction to allow for different window managers to be used

class ActionManipulateWm(BaseAction):
	"""docstring for ActionManipulateWm."""
	def __init__(self):
		super(ActionManipulateWm, self).__init__()
		self.handled_classifier = "manipulate-wm"
		self.requires_updater = False

	@staticmethod
	def _i3_msg(command_type, msg=None):
		"""
		Runs i3-msg and returns the JSON object response
		"""
		assert command_type != "subscribe", "The subscribe command type is invalid here."

		command = ["i3-msg", "-t", command_type]
		if msg:
			command += [msg]
		result = subprocess.Popen(command,
								stdin=subprocess.DEVNULL,
								stdout=subprocess.PIPE,
								stderr=subprocess.DEVNULL)
		out, err = result.communicate()
		return json.loads(out)

	@classmethod
	def get_workspaces(self):
		return self._i3_msg("get_workspaces")

	@classmethod
	def get_outputs(self):
		return self._i3_msg("get_outputs")

	@classmethod
	def get_tree(self):
		return self._i3_msg("get_tree")

	@classmethod
	def get_marks(self):
		return self._i3_msg("get_marks")

	@classmethod
	def find_matching_windows_in_tree(self, i3_tree, query):
		results = []
		if "window" in i3_tree and i3_tree["window"] and "window_properties" in i3_tree:
			if any([prop in i3_tree["window_properties"] and query in i3_tree["window_properties"][prop] for prop in ["class", "instance", "title"]]):
				log.debug(f"Found node in tree: {i3_tree}")
				results += [{
					"id": i3_tree["id"], # C pointer to identify i3 container
					"window": i3_tree["window"], # X11 window reference
				}]
		for node in i3_tree["nodes"]:
			results += self.find_matching_windows_in_tree(node, query)
		return results

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

		# target_token indicates the target entity the request is referencing
		# used for requests like "show me steam" or "switch to the web browser"
		# FIXME: do something more robust
		target_token = utils.find_word(sentence.doc, ["this", "that", "steam", "browser", "firefox", "discord", "telegram"])
		if target_token and target_token.text not in ["this", "that"]:
			matching_windows = self.find_matching_windows_in_tree(self.get_tree(), str(target_token))
			log.info(f"Found {len(matching_windows)} matching windows")

		command = None
		# switching workspaces
		if str(sentence.root) in ["switch", "focus", "show", "pull", "go"]:
			if target_token:
				if len(matching_windows) > 0:
					command = f'i3-msg \'[con_id="{matching_windows[0]["id"]}"] focus\''
				else:
					raise Exception("Could not find any windows matching query")
			elif workspace_token and workspace_number:
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
				if target_token.text in ["this", "that"]:
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
			verb_word = utils.find_word(sentence.doc, ["toggle", "enable", "disable", "make"])
			attribute_word = utils.find_word(sentence.doc, ["fullscreen", "floating", "full", "float"])
			if verb_word and attribute_word:
				verb = verb_word.text
				if verb == "make":
					verb = "enable"
				attribute = attribute_word.text
				if attribute == "full":
					attribute = "fullscreen"
				elif attribute == "float":
					attribute = "floating"
				if target_token and target_token.text not in ["this", "that"]:
					command = f'i3-msg "[con_id=\'{matching_windows[0]["id"]}\'] focus; {attribute} {verb}"'
				else:
					command = f'i3-msg "{attribute} {verb}"'
			else:
				log.error(f"verb_word ({verb_word}) or attribute_word ({attribute_word}) not found")

		return command

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		try:
			command = self.parse(sentence)
		except Exception as e:
			log.exception(e)
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
