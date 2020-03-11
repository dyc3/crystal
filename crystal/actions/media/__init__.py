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
		log.debug(f"{token} child: {child}")
		if child.like_num or child.text == "a":
			try:
				num = int(child.text)
			except ValueError:
				num = utils.text2int(child.text)
	return int(num) * multiplier

class ActionMedia(BaseAction):
	"""docstring for ActionMedia."""
	def __init__(self):
		super(ActionMedia, self).__init__()
		self.handled_classifier = "media"
		self.requires_updater = False

	@classmethod
	def parse(self, sentence):
		if sentence.root.lemma_ in ["skip"]:
			if (sentence.root.n_rights > 0 and list(sentence.root.rights)[0].dep_ == "dobj") or sentence.root.n_rights == 0:
				return "next"

		action = None
		for word in sentence:
			if word.lemma_ in ["play", "resume"]:
				return "play"

			if word.lemma_ in ["pause", "hold"]:
				return "pause"

			if word.lemma_ == "next":
				return "next"

			if word.lemma_ == "previous":
				return "previous"

			if word.lemma_ in ["shuffle", "shuffling"]:
				action = "shuffle"
				break

		if action == "shuffle":
			target_state = True # default
			for word in sentence:
				if word.lemma_ in ["enable", "on"]:
					target_state = True
					break
				elif word.lemma_ in ["disable", "off", "stop"]:
					target_state = False
					break
			return f"shuffle {'On' if target_state else 'Off'}"

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
					if token.text == "to":
						seek_action = ""
						for prepchild in token.children:
							if prepchild.dep_ == "pobj":
								if seconds == None: seconds = 0
								seconds += getSeconds(prepchild)
				elif token.dep_ in ["advmod","amod","acomp"]:
					if token.text in ["back", "backward"]:
						if seek_action == None: seek_action = "-"
					elif token.text in ["ahead", "forward"]:
						if seek_action == None: seek_action = "+"
				elif token.dep_ in ["npadvmod","dobj"]:
					if seconds == None: seconds = 0
					seconds += getSeconds(token)

			return f"position {seek_action}{seconds}"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		command = self.parse(sentence)
		exitcode = utils.runAndPrint(f"playerctl {command}")

		if exitcode == 0:
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, f"playerctl exit code: {exitcode}")

def getAction():
	return ActionMedia()
