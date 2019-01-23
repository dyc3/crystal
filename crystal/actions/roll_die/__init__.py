from crystal.actions import BaseAction
import random
from crystal import feedback
import utils

class ActionRollDie(BaseAction):
	"""docstring for ActionRollDie."""
	def __init__(self):
		super(ActionRollDie, self).__init__()
		self.handled_classifier = "roll-die"
		self.requires_updater = False

	@classmethod
	def parse(self, sentence):
		sides, count = None, None

		if str(sentence[0]) == "roll":
			for child in sentence:
				if "d" in str(child):
					if str(child).lower() == "die":
						count = 1 # TODO: support multiple dice this way
						sides = 6
					else:
						dice_token = child
						d_spl = str(dice_token).split("d")
						if d_spl[0] != "" and d_spl[1] != "":
							count = int(d_spl[0])
							sides = int(d_spl[1])
						else:
							sides = int(str(dice_token).lstrip("d"))

							count_token = dice_token.nbor(-1)
							if str(count_token) == "a":
								count = 1
							else:
								try:
									count = int(str(count_token))
								except:
									count = utils.text2int(str(count_token))
		elif str(sentence.root) == "flip":
			for child in sentence.root.children:
				if child.dep_ in ["dobj"]:
					if child.lemma_ == "coin":
						count = 1
						sides = 2

		return sides, count

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		sides, count = self.parse(sentence)

		if count != None and sides != None and count >= 1 and sides > 1:
			_rolling_str = "rolling {} d{}".format(count, sides)
			print(_rolling_str)
			result = rollDie(sides, count)
			dice = "{} d{}".format(count, sides)
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
