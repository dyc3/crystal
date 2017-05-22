from actions import BaseAction
import random
import feedback

class ActionRollDie(BaseAction):
	"""docstring for ActionRollDie."""
	def __init__(self):
		super(ActionRollDie, self).__init__()
		self.handled_classifier = "roll-die"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		count = None
		sides = None
		dice = None
		if str(sentence.root) == "roll":
			for child in sentence.root.children:
				if child.dep_ in ["nummod", "dobj"]:
					if str(child).lower() == "die":
						count = 1 # TODO: support multiple dice this way
						sides = 6
					else:
						dice = str(child).lower().rstrip("s")
						if "d" in dice:
							#print("dice: "+dice)
							d = dice.split("d")
							if d[1] != "":
								if d[0] != "":
									count = int(d[0])
									sides = int(d[1])
								else:
									if count == None:
										count = 1
									sides = int(dice.lstrip("d"))
						elif child.dep_ == "nummod":
							count = int(str(child))
		elif str(sentence.root) == "flip":
			for child in sentence.root.children:
				if child.dep_ in ["dobj"]:
					if child.lemma_ == "coin":
						count = 1
						sides = 2

		if count != None and sides != None and count >= 1 and sides > 1:
			_rolling_str = "rolling {} d{}".format(count, sides)
			print(_rolling_str)
			result = rollDie(sides, count)
			outputstr = "ROLL: {}\n".format(dice)
			for n in range(len(result)):
				outputstr += "{}{}".format(result[n], (" + " if n != len(result) - 1 else ""))
			if len(result) > 1:
				outputstr += "\ntotal: {}".format(sum(result))
			feedback.ShowNotify(outputstr, _rolling_str)

def getAction():
	return ActionRollDie()

def rollDie(sides, count=1):
	"""
	sides should be an integer
	count should indicate how many dice to roll
	"""
	assert isinstance(sides, int), "sides must be an integer"
	assert isinstance(count, int), "count must be an integer"
	assert sides > 1
	assert count >= 1
	output = []
	for _ in range(count):
		output.append(random.randint(1, sides))
	return output
