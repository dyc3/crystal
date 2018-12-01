from crystal.actions import BaseAction
import utils

class ActionManipulateWm(BaseAction):
	"""docstring for ActionManipulateWm."""
	def __init__(self):
		super(ActionManipulateWm, self).__init__()
		self.handled_classifier = "manipulate-wm"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		utils.printSpacy(sentence)
		command = None
		workspace_alias = ["workspace", "space", "desktop"]
		if str(sentence.root) in ["switch", "focus", "show", "pull", "go"]:
			dobj_token = None
			for child in sentence.root.children:
				if str(child).lower() in workspace_alias:
					if child.dep_ == "dobj":
						dobj_token = child
					elif child.dep_ == "prep":
						for c in child.children:
							if c.dep_== "pobj":
								dobj_token = c
					elif child.dep_ == "ccomp":
						dobj_token = child
			if dobj_token == None:
				print("Unsupported window manager manipulation")
			elif str(dobj_token).lower() in workspace_alias:
				command = None
				for child in dobj_token.children:
					if child.like_num:
						try:
							num = int(str(child))
						except Exception as e:
							num = utils.text2int(str(child))
						command = 'i3-msg "workspace {}"'.format(num)
			elif str(dobj_token).lower() in ["window"]:
				print("TODO: focus windows")
			else:
				print("Unsupported window manager manipulation: dobj_token: {}".format(dobj_token))
		elif str(sentence.root) in ["left", "right"]:
			print("TODO: Unsupported window manager manipulation: {}".format(sentence.root))
			print('Try something like "Focus left window"')

		if command != None:
			exitcode = utils.runAndPrint(command)
			print("exit: ", exitcode)
		else:
			print("error: command == None")
			raise Exception("error: command == None")

def getAction():
	return ActionManipulateWm()
