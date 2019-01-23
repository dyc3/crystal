from crystal.actions import BaseAction
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
			if str(sentence.root.nbor(1)) == "this":
				for word in sentence:
					if word.lemma_ in ["workspace", "space", "desktop"]:
						num_token = word.nbor(1)
						try:
							num = int(str(num_token))
						except:
							num = utils.text2int(str(num_token).lower())
						command = 'i3-msg "move container to workspace number {}"'.format(num)
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
		command = self.parse(sentence)

		if command != None:
			exitcode = utils.runAndPrint(command)
			log.debug("exit: {}".format(exitcode))
		else:
			log.error("command == None")
			raise Exception("error: command == None")

def getAction():
	return ActionManipulateWm()
