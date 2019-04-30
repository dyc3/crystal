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
import wave
import base64
import requests
import snowboydecoder
import crystal.core
import logging
log = logging.getLogger(__name__)

SNOWBOY_TRAIN_ENDPOINT = "https://snowboy.kitt.ai/api/v1/train/"
SAMPLE_RATE = 16000 # this is a standard sample rate used by a lot of speech recognition solutions
SAMPLE_WIDTH = 2 # 2 bytes for 16 bit audio
FRAME_LENGTH = 1024 # i dunno if this is right
WAKEWORD_SILENCE = -2
WAKEWORD_VOICE = 0
WAKEWORD_DETECTED = 1

snowboy_model_file = Path("./crystal.pmdl")
wakeword_audio_dir = Path("./data/wakeword")

__listening = False
__recording_thread = None

def prompt_user_for_recordings() -> list:
	"""
	This prompts the user to record 3 instances of them saying the wake word,
	and saves it to disk. Returns a list of Path of the saved files.
	"""
	if not wakeword_audio_dir.exists():
		wakeword_audio_dir.mkdir(parents=True)

	RECORD_SECONDS = 2.5
	print("We need you to record you saying the wake word \"Crystal\" 3 times.")
	print("We'll record you for {} seconds at a time. Press enter when you are ready to start.".format(RECORD_SECONDS))
	input()
	time.sleep(0.5)

	files = []
	for take in range(3):
		print("Recording take {}...".format(take))
		pa = pyaudio.PyAudio()
		input_stream = pa.open(
			rate=SAMPLE_RATE,
			channels=1,
			format=pyaudio.paInt16,
			input=True,
			frames_per_buffer=FRAME_LENGTH,
			input_device_index=None
		)
		frames = []
		for i in range(0, int(SAMPLE_RATE / FRAME_LENGTH * RECORD_SECONDS)):
			data = input_stream.read(FRAME_LENGTH)
			frames.append(data)
		input_stream.stop_stream()
		input_stream.close()

		target_file = wakeword_audio_dir / "{}.wav".format(take)
		print("Saving to", target_file)
		with wave.open(str(target_file), 'wb') as wf:
			wf.setnchannels(1)
			wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
			wf.setframerate(SAMPLE_RATE)
			wf.writeframes(b''.join(frames))

		files += [target_file]
		time.sleep(0.5)

	return files

def retrain_wakeword_model(files: list) -> Path:
	"""
	Calls the snowboy API to retrain the wake word detector. Returns the Path
	to the wake word model.

	FIXME: Currently does not work.
	"""
	log.info("Retraining wakeword model...")

	def get_wave(path):
		log.debug("Reading {}".format(path))
		with path.open("rb") as infile:
			return base64.b64encode(infile.read())

	data = {
		"name": "Crystal",
		"language": "en",
		"age_group": "20_29",
		"gender": "M",
		"microphone": "??",
		"token": crystal.core.get_config("kitt_ai_token"),
		"voice_samples": [
			{"wave": get_wave(files[0])},
			{"wave": get_wave(files[1])},
			{"wave": get_wave(files[2])}
		]
	}

	response = requests.post(SNOWBOY_TRAIN_ENDPOINT, json=data)
	if response.ok:
		log.info("Success, saving to {}".format(str(snowboy_model_file)))
		with snowboy_model_file.open("w") as outfile:
			outfile.write(response.content)
	else:
		response.raise_for_status()

	return snowboy_model_file

def start_listening():
	global __listening, __recording_thread

	if __listening:
		log.warn("Already listening")
		return

	if not snowboy_model_file.exists():
		log.warn("Wake word model not found, checking for audio files")
		if not wakeword_audio_dir.exists():
			wakeword_files = prompt_user_for_recordings()
		elif not wakeword_audio_dir.is_dir():
			log.critical("{} is a file and not a directory!".format(wakeword_audio_dir))
			raise FileExistsError()
		elif len(list(wakeword_audio_dir.glob("*.wav"))) < 3:
			wakeword_files = prompt_user_for_recordings()
		else:
			wakeword_files = list(wakeword_audio_dir.glob("*.wav"))
		retrain_wakeword_model(wakeword_files)

	log.debug("Starting recording thread...")
	if not __recording_thread:
		__listening = True
		__recording_thread = threading.Thread(name="RecordingThread", target=do_recording, args=())
		__recording_thread.start()
	else:
		log.warn("recording thread already running")

def stop_listening():
	global __listening, __recording_thread
	log.info("Stop listening")

	__listening = False
	if __recording_thread:
		__recording_thread.join()
		__recording_thread = None

def do_recording():
	log.debug("recording thread started")

	wakeword = snowboydecoder.HotwordDetector(str(snowboy_model_file), sensitivity=0.5)

	pa = pyaudio.PyAudio()
	input_stream = pa.open(
		rate=SAMPLE_RATE,
		channels=1,
		format=pyaudio.paInt16,
		input=True,
		frames_per_buffer=FRAME_LENGTH,
		input_device_index=None
	)

	MAX_RECORDING_SECONDS = 10
	SILENCE_THRESHOLD = 10 # number of frames to wait

	wakeword_raw_data = bytes()
	recording_raw_data = bytes()
	active = False
	silence_count = 0
	while __listening:
		# reach in a "chunk"; each chunk contains the specified number of frames (i.e samples)
		data = input_stream.read(FRAME_LENGTH)
		# unpack the chunk to make it processable
		pcm = struct.unpack_from("h" * FRAME_LENGTH, data)

		if active:
			wakeword_raw_data = bytes()
			recording_raw_data += data

			detect_result = wakeword.detector.RunDetection(data)
			# log.debug("wakeword result: {}".format(detect_result))

			if detect_result == WAKEWORD_SILENCE:
				silence_count += 1
			else:
				silence_count = 0

			# check length of recording
			if len(recording_raw_data) >= SAMPLE_RATE * SAMPLE_WIDTH * MAX_RECORDING_SECONDS or silence_count >= SILENCE_THRESHOLD:
				log.debug("Done recording, length {:.2f}s".format(len(recording_raw_data) / SAMPLE_WIDTH / SAMPLE_RATE))
				active = False
				crystal.core.on_recording_finish.fire(recording_raw_data, SAMPLE_RATE, SAMPLE_WIDTH)
		else:
			recording_raw_data = bytes()
			silence_count = 0
			wakeword_raw_data += data
			while len(wakeword_raw_data) > SAMPLE_RATE * SAMPLE_WIDTH * 2: # sample rate * sample width in bytes (2 bytes for 16 bit) * number of seconds
				wakeword_raw_data = wakeword_raw_data[SAMPLE_WIDTH:]
			if len(wakeword_raw_data) > SAMPLE_RATE * SAMPLE_WIDTH:
				result = wakeword.detector.RunDetection(wakeword_raw_data)
				# make sure to include the wakeword in the recording
				# log.debug("wakeword result: {}".format(result))
				if result == WAKEWORD_DETECTED:
					log.debug("Wake word detected")
					crystal.core.on_wakeword.fire()
					active = True
					recording_raw_data = wakeword_raw_data[:]
	log.debug("recording thread exiting")
