import crystal.core
from crystal.core import CrystalStatus
import os
import logging
log = logging.getLogger(__name__)

"""
This outputs feedback to a temporary file in a human readable format. Good for status bars.
"""

def get_tmp_file_path():
	return crystal.core.get_config("feedback_file_path", True) or "/tmp/crystal-status"

last_action_response = None

def render_status():
	with open(get_tmp_file_path(), "w") as f:
		f.write(f"{crystal.core.status.name}")
		if crystal.core.current_utterance:
			f.write(f" - {crystal.core.current_utterance}")
		if last_action_response:
			f.write(f" - {last_action_response.type.name}")
			if last_action_response.message:
				f.write(f": {last_action_response.message}")
		f.truncate()

def on_status_update(status):
	global last_action_response
	if status == CrystalStatus.IDLE:
		last_action_response = None
	render_status()

def on_utterance_update(text):
	render_status()

def on_action_finish(response):
	global last_action_response
	last_action_response = response

def on_core_exit():
	if os.path.exists(get_tmp_file_path()):
		os.remove(get_tmp_file_path())

def register():
	crystal.core.on_status_update += on_status_update
	crystal.core.on_core_exit += on_core_exit
	crystal.core.on_utterance_update += on_utterance_update
	crystal.core.on_action_finish += on_action_finish

def unregister():
	crystal.core.on_status_update -= on_status_update
	crystal.core.on_core_exit -= on_core_exit
	crystal.core.on_utterance_update -= on_utterance_update
	crystal.core.on_action_finish -= on_action_finish
