from crystal.actions import BaseAction
from crystal.actions.responses import *
import random
from crystal import feedback
import utils
import logging
log = logging.getLogger(__name__)

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
			if "d" in str(word).lower() or word.lemma_ == "coin":
				d_spl = str(word).lower().split("d")
				if word.lemma_ == "coin":
					sides = 2
				else:
					if word.lemma_ in ["die", "dice"]:
						sides = 6
					else:
						# get sides and count
						sides = int(d_spl[1])

				if "d" in str(word).lower() and d_spl[0]:
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
			log.info(f"rolling {count} d{sides}")
			result = rollDie(sides, count)
			dice = f"{count} d{sides}"
			outputstr = f"ROLL: {dice}\n"
			for n in range(len(result)):
				outputstr += f"{result[n]}{' + ' if n != len(result) - 1 else ''}"
			if len(result) > 1:
				outputstr += f"\ntotal: {sum(result)}"
			return ActionResponseQuery(outputstr)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, f"count needs to be >= 1, got {count} and sides needs to be > 1, got {sides}")

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
