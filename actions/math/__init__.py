from actions import BaseAction

def text2int(textnum, numwords={}):
	if not numwords:
		units = [
			"zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
			"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
			"sixteen", "seventeen", "eighteen", "nineteen",
		]

		tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

		scales = ["hundred", "thousand", "million", "billion", "trillion"]

		numwords["and"] = (1, 0)
		for idx, word in enumerate(units):	numwords[word] = (1, idx)
		for idx, word in enumerate(tens):	 numwords[word] = (1, idx * 10)
		for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

	current = result = 0
	for word in textnum.split():
		if word not in numwords:
			raise Exception("Illegal word: " + word)

		scale, increment = numwords[word]
		current = current * scale + increment
		if scale > 100:
			result += current
			current = 0

	return result + current

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
						expression += str(text2int(str(child)))
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
						expression += str(text2int(str(token)))
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
