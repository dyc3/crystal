from enum import Enum
from eventhook import EventHook
from abc import ABCMeta
import logging
log = logging.getLogger(__name__)

"""
This file defines event hooks for all events throughout the pipeline, from input to output.
The event handlers are attached and defined elsewhere.
"""

on_utterance_start = EventHook("on_utterance_start")
on_utterance_update = EventHook("on_utterance_update")
on_utterance_finish = EventHook("on_utterance_finish")
on_input_error = EventHook("on_input_error")
on_action_start = EventHook("on_action_start")
on_action_finish = EventHook("on_action_finish")
on_action_error = EventHook("on_action_error")
on_status_update = EventHook("on_status_update")

class CrystalStatus(Enum):
	IDLE = 0
	LISTENING = 1
	BUSY = 2
	ERROR = 3

status = CrystalStatus.IDLE
config = {}

def set_status(s: CrystalStatus):
	global status
	status = s
	log.info("STATUS: {}".format(status))
	on_status_update.fire(status)

def initialize():
	set_status(CrystalStatus.BUSY)

	log.info("Loading...")
	global config
	with open("config.txt", "r") as f:
		for line in f:
			spl = line.split("=")
			config[spl[0]] = spl[1]
	log.debug("Config loaded, found {} items".format(len(config)))

	set_status(CrystalStatus.IDLE)

def get_config(key: str):
	try:
		return config[key]
	except KeyError:
		log.critical("Config does not contain value for {}".format(key))
		return None