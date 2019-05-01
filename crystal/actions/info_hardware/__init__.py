from crystal.actions import BaseAction
from crystal import feedback
import psutil
from pulsectl import Pulse # https://pypi.python.org/pypi/pulsectl
import logging
log = logging.getLogger(__name__)

class ActionInfoHardware(BaseAction):
	"""docstring for ActionInfoHardware."""
	def __init__(self):
		super(ActionInfoHardware, self).__init__()
		self.handled_classifier = "info-hardware"
		self.requires_updater = False

		self.pulse = Pulse('{}-AI'.format("Crystal"))

	#TODO: maybe this should be changed to "info-system" so we can include a lot more info

	@classmethod
	def parse(self, doc) -> (str, list):
		"""
		Returns a tuple: query type, parameters (str, list)

		Available query types:
		* processors
		* memory
		* disks
		* audio_devices
		* network_devices
		"""
		query_type = None
		query_params = []
		for word in doc:
			if word.dep_ == "nsubj" or word.dep_ == "dobj":
				if word.lemma_ in ["processor", "core", "thread"]:
					query_type = "processors"
					if word.lemma_ == "thread":
						query_params.append("logical")
						break

					for child in word.children:
						if child.dep_ == "amod" and str(child) in ["physical", "logical"]:
							query_params.append(str(child))
							break
				elif word.lemma_ in ["memory", "RAM"]:
					query_type = "memory"
				elif word.lemma_ in ["disk", "space", "mount"]:
					query_type = "disks"
				elif word.lemma_ in ["device", "interface"]:
					for child in word.children:
						if child.dep_ == "amod":
							if str(child) in ["audio", "sound"]:
								query_type = "audio_devices"
							elif child.lemma_ in ["network", "internet"]:
								query_type = "network_devices"
							break

		return query_type, query_params

	@classmethod
	def run(self, doc):
		query_type, query_params = self.parse(doc)
		log.info("parsed query: {}, {}".format(query_type, query_params))

		if query_type == None:
			log.error("Failed to parse query_type: {}, {}".format(query_type, query_params))
			raise Exception("info-hardware: Failed to parse query_type: {}, {}".format(query_type, query_params))

		if query_type == "processors":
			if len(query_params) == 0:
				feedback.ShowNotify("{} cores, {} threads".format(psutil.cpu_count(logical=False), psutil.cpu_count(logical=True)))
				return
			if "logical" in query_params:
				feedback.ShowNotify("{} threads".format(psutil.cpu_count(logical=True)))
			elif "physical" in query_params:
				feedback.ShowNotify("{} cores".format(psutil.cpu_count(logical=False)))
			else:
				log.error("Unknown query parameters: {}".format(query_params))
		elif query_type == "memory":
			# TODO: do this better, get parameters
			memvirt = psutil.virtual_memory()
			memswap = psutil.swap_memory()
			unit = 1000000000 # gigabyte
			memstring = "Memory Usage: virtual: {} GB/{} GB ({}%) | swap: {} GB/{} GB ({}%)".format(round(memvirt.used / unit, 1), round(memvirt.total / unit, 1), memvirt.percent,
																	round(memswap.used / unit, 1), round(memswap.total / unit, 1), memswap.percent)
			feedback.ShowNotify(memstring)
		elif query_type == "disks":
			parts = psutil.disk_partitions()
			unit = 1000000000 # gigabyte
			partstring = "Disk Usage:"
			for part in parts:
				# ignore these snap package mounts, I don't know why they exist
				if part.mountpoint.startswith("/snap"):
					continue
				disk = psutil.disk_usage(part.mountpoint)
				partstring += "\n{}: {} GB/{} GB ({}% used)".format(part.mountpoint, round(disk.used / unit, 1), round(disk.total / unit, 1), disk.percent)
			feedback.ShowNotify(partstring)
		elif query_type == "audio_devices":
			# TODO: maybe move this to a seperate "audio" action to handle every thing audio related
			curDefaultSinkName = self.pulse.server_info().default_sink_name
			sinks = self.pulse.sink_list()
			sinks_str = "Sinks:"
			for sink in sinks:
				sinks_str += "\n{}: {} {}".format(sink.index, sink.description, "[DEFAULT]" if sink.name == curDefaultSinkName else "")
			feedback.ShowNotify(sinks_str)

			sources = self.pulse.source_list()
			sources_str = "Sources:"
			for source in sources:
				sources_str += "\n{}: {}".format(source.index, source.description)
			feedback.ShowNotify(sources_str)
		elif query_type == "network_devices":
			# doesn't exactly work :/
			net = psutil.net_if_addrs()
			netstring = "Network Interfaces:"
			for interface in net:
				netstring += "\n{}: IPv4: {} IPv6: {} MAC: {}".format(interface, \
											(str(n) for n in net[interface] if net[interface].family == AddressFamily.AF_INET), \
											(str(n) for n in net[interface] if net[interface].family == AddressFamily.AF_INET6), \
											(str(n) for n in net[interface] if net[interface].family == AddressFamily.AF_LINK))
			feedback.ShowNotify(netstring)

def getAction():
	return ActionInfoHardware()
