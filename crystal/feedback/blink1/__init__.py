import crystal.core
from crystal.core import CrystalStatus
from blink1 import blink1
import logging
log = logging.getLogger(__name__)

b1 = None

def on_status_update(status):
	if status == CrystalStatus.IDLE:
		b1.fade_to_color(100, "black")
	elif status == CrystalStatus.LISTENING:
		b1.fade_to_color(100, "blue")
	elif status == CrystalStatus.BUSY:
		b1.fade_to_color(100, "orange")
	elif status == CrystalStatus.ERROR:
		b1.fade_to_color(100, "red")

def on_core_exit():
	b1.fade_to_color(2000, "black")

def register():
	global b1
	try:
		b1 = blink1.Blink1()
	except blink1.BlinkConnectionFailed as e:
		log.exception(e)
		return

	crystal.core.on_status_update += on_status_update
	crystal.core.on_core_exit += on_core_exit

def unregister():
	crystal.core.on_status_update -= on_status_update
	crystal.core.on_core_exit -= on_core_exit
