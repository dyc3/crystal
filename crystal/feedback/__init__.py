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

enableBlink1 = True
try:
	b1 = blink1.Blink1()
except blink1.BlinkConnectionFailed as e:
	print(e)
	enableBlink1 = False

enableNotify = True
try:
	if os.environ['DISPLAY']:
		Notify.init("Crystal")
except KeyError:
	print('Warning: no $DISPLAY, no notifications will be shown')
	enableNotify = False

def OnStatus(status):
	crystal.core.on_status_update.fire(status)
	if enableBlink1:
		if status == "idle":
			b1.fade_to_color(100, "purple")
		elif status == "listening":
			b1.fade_to_color(100, "blue")
		elif status == "working":
			b1.fade_to_color(100, "orange")
		elif status == "error":
			b1.fade_to_color(100, "red")

def ShowNotify(body, title="Crystal"):
	print("notify: {} - {}".format(title, body))
	if not enableNotify:
		return None
	notification = Notify.Notification.new(title, body, None)
	notification.show()
	return notification

class BaseFeedback(metaclass=ABCMeta):
	"""docstring for BaseFeedback."""
	def __init__(self):
		super(BaseFeedback, self).__init__()

	@classmethod
	@abc.abstractmethod
	def register(self):
		"""
		Each feedback module will individually attach itself to the pipeline here.
		"""
		pass

def load_feedback():
	feedback_modules_str = ["crystal.feedback."+a for a in os.listdir("crystal/feedback") if "." not in a and a != "__pycache__"]

	feedback_modules = []
	for value in feedback_modules_str:
		module = importlib.import_module(name=value)
		module = importlib.reload(module)
		feedback = module.getFeedback()
		feedback_modules.append(feedback)
		feedback.register()

	return feedback_modules