from crystal.actions import BaseAction
from crystal.actions.responses import *
import pywemo
import datetime
from crystal import feedback
import utils
import logging
log = logging.getLogger(__name__)

class DeviceWrapper(object):
	def __init__(self, device):
		super(DeviceWrapper, self).__init__()
		self.internal_device = device

	@property
	def name(self):
		if isinstance(self.internal_device, dict):
			return self.internal_device["name"]
		else:
			return self.internal_device.name

	def set_state(self, state):
		self.internal_device.set_state(state)

	def toggle(self):
		self.internal_device.toggle()

class ActionSmartHome(BaseAction):
	"""docstring for ActionSmartHome."""
	def __init__(self):
		super(ActionSmartHome, self).__init__()
		self.handled_classifier = "smart-home"
		self.requires_updater = True
		self.init()

	@classmethod
	def init(self):
		self.devices = []
		self.last_device_scan = datetime.datetime.now() - datetime.timedelta(seconds=5*60)

	@classmethod
	def get_query_type(self, doc):
		if utils.find_word(doc, ["toggle", "turn"]):
			return "interact"
		if utils.find_word(doc, ["scan", "look"]):
			return "scan"

	@classmethod
	def parse_interact(self, doc):
		verb_token = utils.find_word(doc, ["toggle", "turn"])
		if not verb_token:
			raise Exception("Unable to find verb")
		target_token = None
		for token in doc[verb_token.i + 1:]:
			if token.pos_ == "NOUN":
				target_token = token
				break
		if not target_token:
			raise Exception("Unable to find target")

		if verb_token.text == "toggle":
			objective_state = "toggle"
		else:
			objective_state = 1 if verb_token.nbor(1).text == "on" else 0

		device_name = target_token.text
		target_prev_token = target_token.nbor(-1)
		while target_token.dep_ == "compound":
			device_name += f" {target_token.nbor(1).text}"
			target_token = target_token.nbor(1)
		if target_prev_token.pos_ == "PROPN":
			device_name = f"{target_prev_token.text} {device_name}"
		elif list(target_token.children)[0].dep_ == "poss":
			device_name = f"{list(target_token.children)[0].text} {device_name}"

		return device_name, objective_state

	@classmethod
	def scan_for_devices(self):
		self.devices = pywemo.discover_devices()
		self.devices += [
			pywemo.discovery.device_from_description(f'http://192.168.0.10:{pywemo.ouimeaux_device.probe_wemo("192.168.0.10")}/setup.xml', None),
			pywemo.discovery.device_from_description(f'http://192.168.0.23:{pywemo.ouimeaux_device.probe_wemo("192.168.0.23")}/setup.xml', None),
		]
		self.devices = list([DeviceWrapper(d) for d in self.devices])
		log.info(f"found {len(self.devices)} devices")
		self.last_device_scan = datetime.datetime.now()

	@classmethod
	def select_device(self, name: str):
		for device in self.devices:
			if name in device.name.lower():
				return device

	@classmethod
	def run(self, doc):
		query_type = self.get_query_type(doc)
		if query_type == "interact":
			device_name, objective_state = self.parse_interact(doc)
			log.info(f"Set {device_name}: {objective_state}")
			target_device = self.select_device(device_name)
			log.info(f"Selected: {target_device}")
			if objective_state == "toggle":
				target_device.toggle()
			else:
				target_device.set_state(objective_state)
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		elif query_type == "scan":
			self.scan_for_devices()
			return ActionResponseQuery(f"Found {len(self.devices)} devices")
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, f"Unknown query type: {query_type}")

	@classmethod
	def update(self):
		delta = datetime.datetime.now() - self.last_device_scan
		if delta.total_seconds() < 5 * 60:
			return
		self.scan_for_devices()

def getAction():
	return ActionSmartHome()
