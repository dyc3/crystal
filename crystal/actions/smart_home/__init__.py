from crystal.actions import BaseAction
from crystal.actions.responses import *
import pywemo
import datetime
import requests
import ipaddress
from typing import Union
from crystal import feedback
import utils
import crystal.core.processing
from spacy.tokens import Doc
import logging
log = logging.getLogger(__name__)

class DeviceWrapper(object):
	def __init__(self, ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address], device):
		super(DeviceWrapper, self).__init__()
		if isinstance(ip, str):
			self.ip_address = ipaddress.ip_address(ip)
		else:
			self.ip_address = ip
		self.internal_device = device
		self._name_processed: Doc = None

	@property
	def name(self) -> str:
		if isinstance(self.internal_device, dict):
			return self.internal_device["name"]
		else:
			return self.internal_device.name

	@property
	def name_processed(self) -> Doc:
		if not self._name_processed:
			self._name_processed = crystal.core.processing.parse_nlp(self.name)
		return self._name_processed

	def set_state(self, state) -> None:
		self.internal_device.set_state(state)

	def toggle(self):
		self.internal_device.toggle()

	def health_check(self) -> bool:
		# TODO: check if device is still there
		return True

class ActionSmartHome(BaseAction):
	"""docstring for ActionSmartHome."""
	def __init__(self):
		super(ActionSmartHome, self).__init__()
		self.handled_classifier = "smart-home"
		self.requires_updater = True
		self.init()

	def init(self):
		self.devices = []
		self.last_device_scan = datetime.datetime.now() - datetime.timedelta(seconds=5*60)

	def get_query_type(self, doc: Doc):
		if utils.find_word(doc, ["toggle", "turn"]):
			return "interact"
		if utils.find_word(doc, ["scan", "look", "search", "find"]):
			if utils.find_word(doc, ["how"]):
				return "query"
			return "scan"
		if utils.find_word(doc, ["should", "how", "are", "did", "is", "what", "list"]):
			return "query"
		return "interact"

	def parse_interact(self, doc: Doc):
		verb_token = utils.find_word(doc, ["toggle", "turn"])
		target_token = None
		if verb_token:
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
		else:
			log.warning("no verb found, guessing where the target is")
			action_token = utils.find_word(doc, ["on", "off", "toggle"])
			if action_token:
				target_token = action_token.nbor(-1 if action_token.i == len(doc) - 1 else 1)
				if action_token.text == "toggle":
					objective_state = "toggle"
				else:
					objective_state = 1 if action_token.text == "on" else 0
			else:
				# HACK: assume toggle objective because that's probably what was
				# supposed to happen, but the speech recognition fucked up
				log.debug("No action token, assuming toggle objective")
				objective_state = "toggle"
				# TODO: also assume target token
				nouns = []
				for token in doc:
					if any(token.pos_ == x for x in ["NOUN", "PROPN"]):
						nouns += [token]
				log.debug(f"Found nouns: {nouns}")
				target_token = nouns[-1]

		device_name = target_token.text
		target_prev_token = target_token.nbor(-1) if target_token.i > 0 else None
		while target_token.dep_ == "compound":
			device_name += f" {target_token.nbor(1).text}"
			target_token = target_token.nbor(1)
		if target_prev_token and target_prev_token.pos_ == "PROPN":
			device_name = f"{target_prev_token.text} {device_name}"
		elif list(target_token.children)[0].dep_ == "poss":
			device_name = f"{list(target_token.children)[0].text} {device_name}"

		return device_name, objective_state

	def scan_for_devices(self):
		# NOTE: device discovery doesn't work if ufw is enabled. Idk what the firewall rule to allow the traffic is.
		discovered_devices = pywemo.discover_devices()
		# Manually add devices:
		# self.devices += [pywemo.discovery.device_from_description(f'http://{ip}:{pywemo.ouimeaux_device.probe_wemo(ip)}/setup.xml', None) for ip in ["192.168.0.26", "192.168.0.27", "192.168.0.28"]]
		self.devices = list([DeviceWrapper(d.host, d) for d in discovered_devices])

		log.info(f"found {len(self.devices)} devices")
		self.last_device_scan = datetime.datetime.now()

	def select_device(self, name: str, objective_state: int=None) -> DeviceWrapper:
		name_doc = crystal.core.processing.parse_nlp(name)
		scores = {}
		for idx, device in enumerate(self.devices):
			score = name_doc.similarity(device.name_processed)
			# HACK: boost scores of items in carson's room
			# To fix this, Crystal needs to know what room the request is coming from,
			# and what room each device is located in
			if "carson" in device.name.lower():
				score += 0.075
			log.debug(f"score: {name} <-> {device.name} == {score}")
			scores[idx] = score
		return self.devices[max(scores, key=scores.get)]

	def run(self, doc: Doc):
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

	def update(self):
		delta = datetime.datetime.now() - self.last_device_scan
		if delta.total_seconds() < 10 * 60:
			return
		self.scan_for_devices()

def getAction():
	return ActionSmartHome()
