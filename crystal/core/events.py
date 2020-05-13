import threading
import logging
log = logging.getLogger(__name__)

"""
This file defines event hooks for all events throughout the pipeline, from input to output.
The event handlers are attached and defined elsewhere.
"""

class EventHook(object):

	def __init__(self, name):
		self.name = name
		self.__handlers = []

	def __iadd__(self, handler):
		self.__handlers.append(handler)
		return self

	def __isub__(self, handler):
		self.__handlers.remove(handler)
		return self

	def fire(self, *args, **keywargs):
		log.debug("event triggered: {}, {}, {}".format(self.name, args, keywargs)[:300])
		threads = []
		for handler in self.__handlers:
			thread = threading.Thread(name=f"{self.name}_handler", target=handler, args=args, kwargs=keywargs)
			threads.append(thread)
			thread.start()
		for thread in threads:
			thread.join()

	def clearObjectHandlers(self, inObject):
		for theHandler in self.__handlers:
			if theHandler.im_self == inObject:
				self -= theHandler

on_wakeword = EventHook("on_wakeword")
on_record_buffer = EventHook("on_record_buffer")
on_recording_finish = EventHook("on_recording_finish")
on_utterance_start = EventHook("on_utterance_start")
on_utterance_update = EventHook("on_utterance_update")
on_utterance_finish = EventHook("on_utterance_finish")
on_input_error = EventHook("on_input_error")
on_action_start = EventHook("on_action_start")
on_action_finish = EventHook("on_action_finish")
on_action_error = EventHook("on_action_error")
on_status_update = EventHook("on_status_update")
on_core_exit = EventHook("on_core_exit")