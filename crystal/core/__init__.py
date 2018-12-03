from enum import Enum
from eventhook import EventHook

"""
This file defines event hooks for all events throughout the pipeline, from input to output.
The event handlers are attached and defined elsewhere.
"""

on_utterance_start = EventHook()
on_utterance_update = EventHook()
on_utterance_finish = EventHook()
on_input_error = EventHook()
on_action_start = EventHook()
on_action_finish = EventHook()
on_action_error = EventHook()
on_status_update = EventHook()

# debug event handlers
def print_on_event_trigger(*args, **kwargs):
	print("event triggered:", args, kwargs)
on_utterance_start += print_on_event_trigger
on_utterance_update += print_on_event_trigger
on_utterance_finish += print_on_event_trigger
on_input_error += print_on_event_trigger
on_action_start += print_on_event_trigger
on_action_finish += print_on_event_trigger
on_action_error += print_on_event_trigger
on_status_update += print_on_event_trigger

class CrystalStatus(Enum):
	IDLE = 0
	LISTENING = 1
	BUSY = 2
	ERROR = 3

status = CrystalStatus.IDLE

def set_status(s: CrystalStatus):
	global status
	status = s
	print("STATUS:", status)
	on_status_update.fire(status)