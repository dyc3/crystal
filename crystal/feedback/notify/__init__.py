import crystal.core

import os
import pgi
pgi.install_as_gi()
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify # see: http://www.devdungeon.com/content/desktop-notifications-python-libnotify
import logging
log = logging.getLogger(__name__)

current_utterance_notif = Notify.Notification.new("Crystal", "User:", None)

def on_utterance_start():
	try:
		current_utterance_notif.update("Crystal", "User:", None)
	except:
		log.warn("Failed to show notification")

def on_utterance_update(text):
	if not text.startswith("Crystal"):
		return
	try:
		current_utterance_notif.update("Crystal", "User: {}".format(text), None)
		current_utterance_notif.show()
	except:
		log.warn("Failed to show notification")

def on_utterance_finish(text):
	if not text.startswith("Crystal"):
		return
	try:
		current_utterance_notif.update("Crystal", "User: {}".format(text), None)
		current_utterance_notif.show()
	except:
		log.warn("Failed to show notification")

def on_action_error():
	try:
		notification = Notify.Notification.new("Crystal", "Action failed", None)
		notification.show()
	except:
		log.warn("Failed to show notification")

def register():
	try:
		if os.environ['DISPLAY']:
			Notify.init("Crystal")
	except KeyError:
		log.warn('Warning: no $DISPLAY, no notifications will be shown')
		return

	crystal.core.on_utterance_start += on_utterance_start
	crystal.core.on_utterance_update += on_utterance_update
	crystal.core.on_utterance_finish += on_utterance_finish
	crystal.core.on_action_error += on_action_error

def unregister():
	crystal.core.on_utterance_start -= on_utterance_start
	crystal.core.on_utterance_update -= on_utterance_update
	crystal.core.on_utterance_finish -= on_utterance_finish
	crystal.core.on_action_error -= on_action_error
