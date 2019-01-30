from crystal.actions import BaseAction
from crystal.actions.responses import *
import utils
import logging
log = logging.getLogger(__name__)

def getTimeInSeconds(token):
	log.debug("orth: {}".format(token.orth_))
	multiplier = 1
	if "second" in token.orth_.lower():
		multiplier = 1
	elif "minute" in token.orth_.lower():
		multiplier = 60
	elif "hour" in token.orth_.lower():
		multiplier = 60 * 60
	elif "day" in token.orth_.lower():
		multiplier = 60 * 60 * 24
	elif str(token) in ["beginning", "start"]:
		multiplier = 0
	#return int(str(token).split(" ")[0])
	num = 0
	for child in token.children:
		log.debug("{} child: {}".format(token, child))
		if child.dep_ == "nummod":
			num = str(child)
	return int(num) * multiplier

class ActionMedia(BaseAction):
	"""docstring for ActionMedia."""
	def __init__(self):
		super(ActionMedia, self).__init__()
		self.handled_classifier = "media"
		self.requires_updater = False

	@classmethod
	def parse(self, sentence):
		if sentence.root.lemma_ in ["play", "resume"]:
			return "play"
		elif sentence.root.lemma_ in ["pause", "hold"]:
			return "pause"
		elif sentence.root.lemma_ in ["skip"]:
			if (sentence.root.n_rights > 0 and list(sentence.root.rights)[0].dep_ == "dobj") or sentence.root.n_rights == 0:
				return "next"

		# media seeking
		if sentence.root.lemma_ in ["go", "seek", "skip"]:
			seek_action = None
			seconds = None

			def getSeconds(token):
				sec = 0
				sec += getTimeInSeconds(token)
				for child in token.children:
					if child.dep_ in ["conj","appos"]:
						sec += getSeconds(child)
				return sec

			for token in sentence:
				if token.dep_ == "prep":
					if str(token) == "to":
						seek_action = ""
						for prepchild in token.children:
							if prepchild.dep_ == "pobj":
								if seconds == None: seconds = 0
								seconds += getSeconds(prepchild)
				elif str(token.dep_) in ["advmod","amod","acomp"]:
					if str(token) in ["back", "backward"]:
						if seek_action == None: seek_action = "-"
					elif str(token) in ["ahead", "forward"]:
						if seek_action == None: seek_action = "+"
				elif token.dep_ in ["npadvmod","dobj"]:
					if seconds == None: seconds = 0
					seconds += getSeconds(token)

			return "position {}{}".format(seek_action, seconds)

		for word in sentence:
			if word.lemma_ == "next":
				return "next"

			if word.lemma_ == "previous":
				return "previous"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		command = self.parse(sentence)
		exitcode = utils.runAndPrint("playerctl {}".format(command))

		if exitcode == 0:
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, "playerctl exit code: {}".format(exitcode))

def getAction():
	return ActionMedia()
