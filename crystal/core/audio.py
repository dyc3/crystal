"""
Handles recording and passes raw audio into the input modules. Tells
the system when utterances start and when they stop.

The default maximum utterance length is 10 seconds, but this should be
configurable.

Here's how it should work:

1.	On system startup, calibrate the noise/energy threshold, and start
	snowboy wake word detector.
2.	When the wake word is detected, start recording, and trigger the
	system event on_wakeword.
3.	Stop recording after the audio's energy goes below the energy
	threshold for 1 second, or if the maximum utterance length is reached.
4.	Pass recorded audio into the system via the event on_utterance_finish.

When starting the wake word detector, we need a model to make it work.
If no model is found, prompt the user to say the wake word 3 times, and
save those audio files to disk. Call the snowboy API to train a new model,
using those audio files, and save the returned model to disk.
"""

import time, struct
from pathlib import Path
import threading
import pyaudio
import crystal.core
import logging
log = logging.getLogger(__name__)

SNOWBOY_TRAIN_ENDPOINT = "https://snowboy.kitt.ai/api/v1/train/"
snowboy_model_file = Path("./hotword.pmdl")
wakeword_audio_dir = Path("./data/wakeword")

__listening = False
__listening_thread = None

def prompt_user_for_recordings() -> list:
	"""
	This prompts the user to record 3 instances of them saying the wake word,
	and saves it to disk. Returns a list of Path of the saved files.
	"""
	if not wakeword_audio_dir.exists():
		wakeword_audio_dir.mkdir(parents=True)

def retrain_wakeword_model(files: list) -> Path:
	"""
	Calls the snowboy API to retrain the wake word detector. Returns the Path
	to the wake word model.
	"""

def start_listening():
	if not snowboy_model_file.exists():
		log.warn("Wake word model not found, checking for audio files")
		if not wakeword_audio_dir.exists():
			prompt_user_for_recordings()
		elif not wakeword_audio_dir.is_dir():
			log.critical("{} is a file and not a directory!".format(wakeword_audio_dir))
			raise FileExistsError()
		elif len(wakeword_audio_dir.glob("*.wav")) < 3:
			prompt_user_for_recordings()

# 	if not __listening:
# 		log.debug("starting listener thread")
# 		__listening_thread = threading.Thread(name="ListeningThread", target=do_listening, args=())
# 		__listening_thread.start()

# def stop_listening():
# 	if __listening:
# 		__listening = False
# 		__listening_thread.join()
# 		__listening_thread = None

def do_listening():
	log.debug("listener thread started")
	__listening = True

	SAMPLE_RATE = 16000 # this is a standard sample rate used by a lot of speech recognition solutions
	FRAME_LENGTH = 1024 # i dunno if this is right

	pa = pyaudio.PyAudio()
	input_stream = pa.open(
		rate=SAMPLE_RATE,
		channels=1,
		format=pyaudio.paInt16,
		input=True,
		frames_per_buffer=FRAME_LENGTH,
		input_device_index=None
	)

	while __listening:
		# reach in a "chunk"; each chunk contains the specified number of frames (i.e samples)
		pcm = input_stream.read(FRAME_LENGTH)
		# unpack the chunk to make it processable
		pcm = struct.unpack_from("h" * FRAME_LENGTH, pcm)

