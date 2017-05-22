from actions import BaseAction
import utils

class ActionMath(BaseAction):
	"""docstring for ActionMath."""
	def __init__(self):
		super(ActionMath, self).__init__()
		self.handled_classifier = "math"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		expression = ""
		if str(sentence.root) == "divide":
			for child in sentence.root.children:
				if child.dep_ == "dobj":
					try:
						value = int(str(child))
						expression += str(value)
					except Exception as e:
						expression += str(utils.text2int(str(child)))
					expression += "/"
				elif child.dep_ == "prep" and str(child) == "by":
					try:
						value = int(str(next(child.children)))
						expression += str(value)
					except Exception as e:
						expression += str(text2int(str(next(child.children))))
		else:
			for token in sentence:
				print("{} - {}, {}".format(str(token), token.pos_, token.dep_))
				if token.pos_ == "NUM":
					try:
						value = int(str(token))
						expression += str(value)
					except Exception as e:
						expression += str(utils.text2int(str(token)))
				elif token.pos_ in ["CONJ", "VERB"] or token.dep_ == "quantmod":
					if str(token) == "plus":
						expression += "+"
					elif str(token) == "minus":
						expression += "-"
					elif str(token) == "times":
						expression += "*"
					elif str(token.lemma_) == "divide" or str(token) == "over":
						expression += "/"
				elif token.pos_ == "SYM":
					expression += str(token)
		print("expression: {}".format(expression))
		solution = eval(expression) # FIXME: potential security exploit here
		print("solution: {}".format(solution))

def getAction():
	return ActionMath()
