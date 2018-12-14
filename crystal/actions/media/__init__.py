from crystal.actions import BaseAction
import utils
import logging
log = logging.getLogger(__name__)

class ActionMedia(BaseAction):
	"""docstring for ActionMedia."""
	def __init__(self):
		super(ActionMedia, self).__init__()
		self.handled_classifier = "media"

	@classmethod
	def parse(self, sentence):
		if sentence.root.lemma_ in ["play", "resume"]:
			return "play"
		elif sentence.root.lemma_ in ["pause", "hold"]:
			return "pause"
		elif sentence.root.lemma_ in ["skip"]:
			return "next"

		for word in sentence:
			if word.lemma_ == "next":
				return "next"

			if word.lemma_ == "previous":
				return "previous"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		command = self.parse(sentence)
		utils.runAndPrint("playerctl {}".format(command))

def getAction():
	return ActionMedia()
