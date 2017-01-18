from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
import websockets
import threading
import audioop

class WatsonSpeechRecognizer(BaseSpeechRecognizer):
	"""docstring for WatsonSpeechRecognizer."""
	def __init__(self, username, password):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished

		self.username = username
		self.password = password

		self.status = "not-speaking"
		self.isRunning = False

	def Start(self):
		if not self.isRunning:
			headers = {}
			print("Watson: getting token...")
			headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://stream.watsonplatform.net","speech-to-text",self.username,self.password)
			print("Watson: connecting...")
			self.websocket = websockets.connect("wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize",extra_headers=headers)
			self.threadReceiver = threading.Thread(name="watson-receiver")
			self.threadReceiver.run = self._doThreadReceiver
			self.isRunning = True
			self.status = "not-speaking"
			self._notSpeakingTicks = 0
			self.threadReceiver.Start()

	def Stop(self):
		if self.isRunning:
			self.isRunning = False
			self.threadReceiver.join()

	def GiveFrame(self, frame, speaking_power=200):
		frame_power = audioop.rms(frame, 2)
		if self.status == "not-speaking" and frame_power >= speaking_power:
			self.status = "speaking"
			self._notSpeakingTicks = 0
			self.websocket.send('{action:"start", content-type="audio/flac"}')

		if self.status == "speaking":
			self.websocket.send(frame)
			if frame_power >= speaking_power:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 80:
			self.status = "not-speaking"
			self.websocket.send('{action:"stop"}')


	def _doThreadReceiver(self):

		while self.isRunning:
			received = websockets.recv()
			print("received:",received)
			result = json.loads(received)
			if not result.results[0].final:
				self.onSpeech.fire(result.results[0].alternatives[0].transcript)
			else:
				self.onFinish.fire(result.results[0].alternatives[0].transcript)


	def getAuthenticationToken(self, hostname, serviceName, username, password):
		uri = hostname + "/authorization/api/v1/token?url=" + hostname + '/' \
			  + serviceName + "/api"
		uri = uri.replace("wss://", "https://")
		uri = uri.replace("ws://", "https://")
		print(uri)
		resp = requests.get(uri, auth=(username, password), verify=False,
							headers={'Accept': 'application/json'},
							timeout=(30, 30))
		print(resp.text)
		jsonObject = resp.json()
		return jsonObject['token']
