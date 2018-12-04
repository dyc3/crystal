from crystal.actions import BaseAction
import utils

class ActionManipulateWm(BaseAction):
	"""docstring for ActionManipulateWm."""
	def __init__(self):
		super(ActionManipulateWm, self).__init__()
		self.handled_classifier = "manipulate-wm"

	@classmethod
	def parse(self, sentence):
		"""
		Returns a i3-msg command with arguments to complete the action.
		"""
		command = None
		if str(sentence.root) in ["switch", "focus", "show", "pull", "go"]:
			for word in sentence:
				if word.lemma_ in ["workspace", "space", "desktop"]:
					num_token = word.nbor(1)
					try:
						num = int(str(num_token))
					except:
						num = utils.text2int(str(num_token).lower())
					command = 'i3-msg "workspace {}"'.format(num)

		return command

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		utils.printSpacy(sentence)
		command = self.parse(sentence)

		if command != None:
			exitcode = utils.runAndPrint(command)
			print("exit: ", exitcode)
		else:
			print("error: command == None")
			raise Exception("error: command == None")

def getAction():
	return ActionManipulateWm()
