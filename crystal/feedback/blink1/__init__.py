import crystal.core
from crystal.core import CrystalStatus
from blink1 import blink1

b1 = None

def on_status_update(status):
	print("STATUS:", status)
	if status == CrystalStatus.IDLE:
		b1.fade_to_color(100, "purple")
	elif status == CrystalStatus.LISTENING:
		b1.fade_to_color(100, "blue")
	elif status == CrystalStatus.BUSY:
		b1.fade_to_color(100, "orange")
	elif status == CrystalStatus.ERROR:
		b1.fade_to_color(100, "red")

def register():
	global b1
	try:
		b1 = blink1.Blink1()
	except blink1.BlinkConnectionFailed as e:
		print(e)
		return

	crystal.core.on_status_update += on_status_update

def unregister():
	crystal.core.on_status_update -= on_status_update