from abc import ABCMeta
import abc
import os, importlib
import pgi
pgi.install_as_gi()
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify # see: http://www.devdungeon.com/content/desktop-notifications-python-libnotify
from blink1 import blink1

import crystal.core

enableNotify = True
try:
	if os.environ['DISPLAY']:
		Notify.init("Crystal")
except KeyError:
	print('Warning: no $DISPLAY, no notifications will be shown')
	enableNotify = False

def OnStatus(status):
	print("WARNING: OnStatus has been deprecated, remove the call and replace it with crystal.core.set_status")
	if status == "idle":
		crystal.core.set_status(crystal.core.CrystalStatus.IDLE)
	elif status == "listening":
		crystal.core.set_status(crystal.core.CrystalStatus.LISTENING)
	elif status == "working":
		crystal.core.set_status(crystal.core.CrystalStatus.BUSY)
	elif status == "error":
		crystal.core.set_status(crystal.core.CrystalStatus.ERROR)

def ShowNotify(body, title="Crystal"):
	print("notify: {} - {}".format(title, body))
	if not enableNotify:
		return None
	notification = Notify.Notification.new(title, body, None)
	notification.show()
	return notification

def load_feedback():
	feedback_modules_str = ["crystal.feedback."+a for a in os.listdir("crystal/feedback") if "." not in a and a != "__pycache__"]

	feedback_modules = []
	for value in feedback_modules_str:
		module = importlib.import_module(name=value)
		feedback = importlib.reload(module)
		feedback_modules.append(feedback)
		feedback.register()

	return feedback_modules