from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
import threading
import audioop
from audio import get_flac_data, get_raw_data
import numpy
import websocket
import time

class WatsonSpeechRecognizer(BaseSpeechRecognizer):
	singleton = None
	"""docstring for WatsonSpeechRecognizer."""
	def __init__(self, username, password):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished

		self.username = username
		self.password = password

		self.status = "not-speaking"
		self._notSpeakingTicks = 0
		self.isRunning = False

		self.hostname = "stream.watsonplatform.net"
		# self.hostname = "general-cardude419.c9users.io"

		self.websocket = None

		if not WatsonSpeechRecognizer.singleton:
			WatsonSpeechRecognizer.singleton = self
		else:
			self = WatsonSpeechRecognizer.singleton

		def _onFinish(text):
			self.status = "not-speaking"
			self.websocket.send('{"action":"stop"}'.encode('utf8'))
			self.websocket.close()
		self.onFinish += _onFinish

	def Start(self):
		print("Watson: isRunning =", self.isRunning)
		if not self.isRunning:
			headers = {}
			print("Watson: getting token...")
			headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://"+ self.hostname,"speech-to-text",self.username,self.password)
			self.websocket_headers = headers

			self.threadReceiver = threading.Thread(name="watson-speech-receiver")
			self.threadReceiver.run = self._doThreadReceiver
			self.isRunning = True
			self.status = "not-speaking"
			self._notSpeakingTicks = 0
			self._speakingBuffer = [] # array of frames to be sent if we are actually speaking
			self.threadReceiver.start()

	def Stop(self):
		if self.isRunning:
			print("STOPPING")
			self.isRunning = False
			self.threadReceiver.join()
			self.websocket.close()

	def GiveFrame(self, frame, sample_rate, sample_width, power_threshold=300):

		def doSendMessage(text):
			if self.websocket == None or not self.websocket.connected:
				# return False
				self._doConnect()
				if not self.websocket.connected:
					return False
			self.websocket.send(text.encode('utf8'))
			return True

		def doSendFrame(frame, sample_rate, sample_width):
			if self.websocket == None or not self.websocket.connected:
				# return False
				self._doConnect()
				if not self.websocket.connected:
					return False
			raw_data = get_raw_data(frame, sample_rate, sample_width)
			if len(raw_data) > 0:
				self.websocket.send_binary(raw_data)
			return True

		frame_power = audioop.rms(frame, sample_width)
		# add to frame buffer
		if self.status == "not-speaking" and frame_power >= power_threshold:
			self._speakingBuffer.append(frame)
		else:
			self._speakingBuffer = []

		# determine if we should start sending data
		if self.status == "not-speaking" and frame_power >= power_threshold and len(self._speakingBuffer) > 4:
			self.status = "speaking"
			self._notSpeakingTicks = 0
			doSendMessage('{"action":"start", "content-type":"audio/l16;rate=16000;channels=2;", "interim_results":true, "profanity_filter":false}')

		if self.status == "speaking":
			if len(self._speakingBuffer) > 0:
				if doSendFrame(numpy.concatenate([self._speakingBuffer]).tobytes(), sample_rate, sample_width):
					self._speakingBuffer = []
			doSendFrame(frame, sample_rate, sample_width)
			if frame_power >= power_threshold:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 10:
			self.status = "not-speaking"
			doSendMessage('{"action":"stop"}')

	def _doThreadReceiver(self):
		while self.isRunning:
			if self.websocket != None and self.websocket.connected:
				text = self.websocket.recv()
				if len(text) == 0:
					continue
				# print("Watson: Text received: {0}".format(text))
				result = json.loads(text)
				if 'error' not in result:
					if 'results' in result and len(result['results']) > 0:
						if not result['results'][0]['final']:
							self.onSpeech.fire(result['results'][0]['alternatives'][0]['transcript'])
						else:
							self.onFinish.fire(result['results'][0]['alternatives'][0]['transcript'])
					elif 'state' in result:
						# print("Watson: server state:", result['state'])
						pass
				else:
					print("Watson received error:", result['error'])
			else:
				time.sleep(0.1)

	def getAuthenticationToken(self, hostname, serviceName, username, password):
		uri = hostname + "/authorization/api/v1/token?url=" + hostname + '/' + \
			  serviceName + "/api"
		uri = uri.replace("wss://", "https://")
		uri = uri.replace("ws://", "https://")
		# print(uri)
		resp = requests.get(uri, auth=(username, password), verify=False,
							headers={'Accept': 'application/json'}, timeout=(30, 30))
		# print(resp.text)
		jsonObject = resp.json()
		return jsonObject['token']

	def _doConnect(self):
		if self.websocket != None and self.websocket.connected:
			print("Already connected.")
			return
		uri = "wss://"+ self.hostname +"/speech-to-text/api/v1/recognize"
		self.websocket = websocket.create_connection(uri, header=self.websocket_headers)
