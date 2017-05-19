import datetime
from pulsectl import Pulse
from actions import BaseAction

pulse = Pulse('Crystal-AI')

class ActionVolumeSet(BaseAction):
	"""docstring for ActionVolumeSet."""
	def __init__(self):
		super(ActionVolumeSet, self).__init__()
		self.handled_classifier = "volume-set"

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
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
			print("percent unspecified, using arbitrary percentage: {0}".format(percent))
		for sink in pulse.sink_list():
			if sink.name == pulse.server_info().default_sink_name:
				if volumeaction == "increase":
					percent = sink.volume.value_flat + percent
				elif volumeaction == "decrease":
					percent = sink.volume.value_flat - percent
				print("setting default sink volume: {} -> {}".format(sink.volume.value_flat, percent))
				pulse.volume_set_all_chans(sink, percent)
				break

def getAction():
	return ActionVolumeSet()
