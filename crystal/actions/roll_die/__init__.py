from crystal.actions import BaseAction
from crystal.actions.responses import *
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
	def parse(self, doc):
		sides, count = None, None

		for word in doc:
			if word.lemma_ == "flip":
				count = 1 # TOOD: flip multiple coins
				sides = 2
				break
			if "d" in str(word).lower():
				d_spl = str(word).lower().split("d")
				if str(word.lemma_).lower() in ["die", "dice"]:
					sides = 6
				else:
					# get sides and count
					sides = int(d_spl[1])

				if d_spl[0]:
					count = int(d_spl[0])
				else:
					# get count from previous token
					count_token = word.nbor(-1)
					if str(count_token) == "a":
						count = 1
					else:
						try:
							count = int(str(count_token))
						except ValueError:
							count = utils.text2int(str(count_token))
		return sides, count

	@classmethod
	def run(self, doc):
		# sentence = next(doc.sents)
		sides, count = self.parse(doc)

		if count and sides and count >= 1 and sides > 1:
			_rolling_str = "rolling {} d{}".format(count, sides)
			print(_rolling_str)
			result = rollDie(sides, count)
			dice = "{} d{}".format(count, sides)
			outputstr = "ROLL: {}\n".format(dice)
			for n in range(len(result)):
				outputstr += "{}{}".format(result[n], (" + " if n != len(result) - 1 else ""))
			if len(result) > 1:
				outputstr += "\ntotal: {}".format(sum(result))
			# feedback.ShowNotify(outputstr, _rolling_str)
			return ActionResponseQuery(outputstr)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, "count needs to be >= 1, got {} and sides needs to be > 1, got {}".format(count, sides))

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
