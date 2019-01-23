import datetime
from pulsectl import Pulse
from crystal.actions import BaseAction
import utils
import logging
log = logging.getLogger(__name__)

pulse = Pulse('Crystal-AI')

class ActionVolumeSet(BaseAction):
	"""docstring for ActionVolumeSet."""
	def __init__(self):
		super(ActionVolumeSet, self).__init__()
		self.handled_classifier = "volume-set"
		self.requires_updater = False

	@classmethod
	def parse(self, current_volume: float, sentence) -> float:
		"""
		current_voiume: The current volume in this context.
		sentence: spaCy parsed sentence

		returns the target volume as float, or a string, either "mute" or "unmute"
		"""
		assert isinstance(current_volume, float)
		assert not isinstance(sentence, str)

		for word in sentence:
			if word.lemma_ in ["mute", "unmute"]:
				return word.lemma_

		percent = None
		volumeaction = None
		if str(sentence.root) == "set" or str(sentence.root) == "increase" or str(sentence.root) == "decrease":
			if volumeaction == None: volumeaction = str(sentence.root)
		elif str(sentence.root) == "turn":
			for child in sentence.root.children:
				if child.dep_ == "prt":
					if str(child) == "up":
						if volumeaction == None: volumeaction = "increase"
					elif str(child) == "down":
						if volumeaction == None: volumeaction = "decrease"
		elif str(sentence.root) == "volume":
			for child in sentence.root.children:
				if str(child) in ["increase", "decrease"]:
					volumeaction = str(child)

		for child in sentence.root.children:
			#print ("child: {0}: {1}".format(child, child.dep_))
			if child.dep_ == "prep":
				if str(child) == "to":
					volumeaction = "set"
				elif str(child) == "by":
					pass
				else:
					continue
				for prepchild in child.children:
					#print ("prepchild: {0}: {1}".format(prepchild, prepchild.dep_))
					if prepchild.dep_ == "pobj":
						#print(str(prepchild))
						if str(prepchild) == "%" or str(prepchild) == "percent":
							for n in prepchild.children:
								#print ("n: {0}: {1}".format(n, n.dep_))
								if n.dep_ == "nummod":
									p = str(n)
									break
						else:
							p = str(prepchild)
						percent = float(p.rstrip('%')) / 100
						break

		if percent == None:
			percent = 0.10
			log.debug("percent unspecified, using arbitrary percentage: {}".format(percent))

		if volumeaction == "increase":
			return round(current_volume + percent, 2)
		elif volumeaction == "decrease":
			return round(current_volume - percent, 2)

		return round(percent, 2)

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		for sink in pulse.sink_list():
			if sink.name == pulse.server_info().default_sink_name:
				result = self.parse(sink.volume.value_flat, sentence)
				if result == "mute":
					log.info("muting default sink")
					utils.runAndPrint("pactl set-sink-mute @DEFAULT_SINK@ on")
				elif result == "unmute":
					log.info("unmuting default sink")
					utils.runAndPrint("pactl set-sink-mute @DEFAULT_SINK@ off")
				else:
					percent = result
					log.info("setting default sink volume: {} -> {}".format(sink.volume.value_flat, percent))
					pulse.volume_set_all_chans(sink, percent)
				break

def getAction():
	return ActionVolumeSet()
