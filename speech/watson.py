from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
import websockets
import threading
import audioop
import asyncio

class WatsonSpeechRecognizer(BaseSpeechRecognizer):
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

		# self.hostname = "stream.watsonplatform.net"
		self.hostname = "general-cardude419.c9users.io"

	def Start(self):
		if not self.isRunning:
			headers = {}
			print("Watson: getting token...")
			headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://"+ self.hostname,"speech-to-text",self.username,self.password)
			print("Watson: connecting...")
			with websockets.connect("wss://"+ self.hostname +"/speech-to-text/api/v1/recognize",extra_headers=headers) as ws:
				self.websocket = ws
				print(ws)
			# self.websocket = yield from websockets.connect("wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize",extra_headers=headers)
			self.threadReceiver = threading.Thread(name="watson-receiver")
			self.threadReceiver.run = self._doThreadReceiver
			self.isRunning = True
			self.status = "not-speaking"
			self._notSpeakingTicks = 0
			self.threadReceiver.start()

	def Stop(self):
		if self.isRunning:
			print("STOPPING")
			self.isRunning = False
			self.threadReceiver.join()

	def GiveFrame(self, frame, power_threshold=300):
		frame_power = audioop.rms(frame, 2)
		if self.status == "not-speaking" and frame_power >= power_threshold:
			self.status = "speaking"
			self._notSpeakingTicks = 0
			yield from self.websocket.send('{action:"start", content-type="audio/flac"}')

		if self.status == "speaking":
			yield from self.websocket.send(frame)
			if frame_power >= power_threshold:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 280:
			self.status = "not-speaking"
			yield from self.websocket.send('{action:"stop"}')


	def _doThreadReceiver(self):

		while self.isRunning:
			received = yield from self.websocket.recv()
			print("received:",received)
			result = json.loads(received)
			if not result.results[0].final:
				self.onSpeech.fire(result.results[0].alternatives[0].transcript)
			else:
				self.onFinish.fire(result.results[0].alternatives[0].transcript)

		self.websocket.close()


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
