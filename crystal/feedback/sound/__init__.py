import random, os
import crystal.core
from crystal.core import CrystalStatus
import simpleaudio as sa # http://simpleaudio.readthedocs.io/en/latest/simpleaudio.html#api

nowPlaying = None

def _playfile(file):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file = dir_path + "/" + file

	global nowPlaying
	print("Voice: playing {0}".format(file))

	if nowPlaying and nowPlaying.is_playing():
		nowPlaying.stop()

	wave_obj = sa.WaveObject.from_wave_file(file)
	nowPlaying = wave_obj.play()
	return nowPlaying

def listen_start():
	_playfile("sound/listen-start.wav")

def listen_stop():
	_playfile("sound/listen-stop.wav")

def processing():
	_playfile("sound/processing.wav")

def ack():
	_playfile("sound/acknowledge-generic.wav")

def ack_bad():
	_playfile("sound/acknowledge-bad.wav")

def ack_list():
	_playfile("sound/acknowledge-list.wav")

def ack_cancel():
	_playfile("sound/acknowledge-cancel.wav")

def scroll_short():
	_playfile("sound/scroll-short.wav")

def sayaffirmative():
	_playfile("sound/affirmative.wav")

def saynegative():
	_playfile("sound/negative.wav")

def sayexecuted():
	_playfile("sound/executed.wav")

def sayworking():
	_playfile("sound/working.wav")

def error():
	f = "sound/" + random.choice(["error-1.wav"]) #, "error-2.wav", "error-3.wav"
	_playfile(f)

def on_status_update(status):
	if status == CrystalStatus.BUSY:
		processing()
	elif status == CrystalStatus.ERROR:
		error()

def on_action_finish(result):
	if str(result).lower() == "yes" or result == True:
		sayaffirmative()
	elif str(result).lower() == "no" or result == False:
		saynegative()
	else:
		ack()

def register():
	crystal.core.on_status_update += on_status_update
	crystal.core.on_action_finish += on_action_finish

def unregister():
	crystal.core.on_status_update -= on_status_update
	crystal.core.on_action_finish -= on_action_finish