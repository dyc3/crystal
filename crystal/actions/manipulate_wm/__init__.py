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
		command = None
		# switching workspaces
		if str(sentence.root) in ["switch", "focus", "show", "pull", "go"]:
			for word in sentence:
				if word.lemma_ in ["workspace", "space", "desktop"]:
					num_token = word.nbor(1)
					try:
						num = int(str(num_token))
					except:
						num = utils.text2int(str(num_token).lower())
					command = 'i3-msg "workspace {}"'.format(num)
		# moving windows to other workspaces
		elif str(sentence.root) in ["move", "put"]:
			target_workspace = None
			for word in sentence:
				if word.lemma_ in ["workspace", "space", "desktop"]:
					num_token = word.nbor(1)
					try:
						target_workspace = int(str(num_token))
					except:
						target_workspace = utils.text2int(str(num_token).lower())
			if not target_workspace:
				raise Exception("Unable to parse for target workspace")
			if str(sentence.root.nbor(1)) == "this":
				command = 'i3-msg "move container to workspace number {}"'.format(target_workspace)
		elif sentence.root.lemma_ in ["kill", "close", "quit"]:
			command = 'i3-msg "kill"'
		else:
			for word in sentence:
				if str(word) == "toggle":
					if str(word.nbor(1)) in ["fullscreen"]:
						command = 'i3-msg "fullscreen toggle"'
					elif str(word.nbor(1)) in ["floating"]:
						command = 'i3-msg "floating toggle"'

		return command

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		utils.printSpacy(sentence)
		try:
			command = self.parse(sentence)
		except Exception as e:
			return ActionResponseBasic(ActionResponseType.FAILURE, "Parsing failed: {}".format(e.message))

		if command != None:
			exitcode = utils.runAndPrint(command)
			log.debug("exit: {}".format(exitcode))
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		else:
			log.error("command == None")
			return ActionResponseBasic(ActionResponseType.FAILURE, "command == None")

def getAction():
	return ActionManipulateWm()
