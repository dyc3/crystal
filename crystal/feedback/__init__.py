import os
import pgi
pgi.install_as_gi()
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify # see: http://www.devdungeon.com/content/desktop-notifications-python-libnotify
from blink1 import blink1

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