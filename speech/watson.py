from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
import websockets
import threading
import audioop
import asyncio

class WatsonSpeechClientProtocol(WebSocketClientProtocol):

	def onConnect(self, response):
		print("Watson: Server connected: {0}".format(response.peer))

	def onOpen(self):
		print("Watson: WebSocket connection open.")

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			text = payload.decode('utf8'))
			print("Watson: Text message received: {0}".format(text)

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))

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

		self.hostname = "stream.watsonplatform.net"
		# self.hostname = "general-cardude419.c9users.io"

	def Start(self):
		print("Watson: isRunning =", self.isRunning)
		if not self.isRunning:
			headers = {}
			print("Watson: getting token...")
			headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://"+ self.hostname,"speech-to-text",self.username,self.password)
			print("Watson: connecting...")
			# gotta do all this extra junk because websockets.connect is all async and shit
			# and you have to do this for ALL async functions to run syncronously
			loop = asyncio.get_event_loop()
			self.websocket = loop.run_until_complete(websockets.connect("wss://"+ self.hostname +"/speech-to-text/api/v1/recognize",extra_headers=headers))
			loop.close()
			print("Watson: connected")
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
		try:
			loop = asyncio.get_event_loop()
		except RuntimeError as e:
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			# loop.run_forever()
		frame_power = audioop.rms(frame, 2)
		if self.status == "not-speaking" and frame_power >= power_threshold:
			self.status = "speaking"
			self._notSpeakingTicks = 0
			# self.websocket.send('{action:"start", content-type="audio/flac"}')
			loop.run_until_complete(self.websocket.send('{action:"start", content-type="audio/flac"}'))

		if self.status == "speaking":
			# self.websocket.send(frame)
			loop.run_until_complete(self.websocket.send(frame))
			if frame_power >= power_threshold:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 280:
			self.status = "not-speaking"
			# self.websocket.send('{action:"stop"}')
			loop.run_until_complete(self.websocket.send('{action:"stop"}'))

		loop.stop()


	def _doThreadReceiver(self):
		try:
			loop = asyncio.get_event_loop()
		except RuntimeError as e:
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)

		while self.isRunning:
			received = loop.run_until_complete(self.websocket.recv())
			print("received:",received)
			result = json.loads(received)
			if not result.results[0].final:
				self.onSpeech.fire(result.results[0].alternatives[0].transcript)
			else:
				self.onFinish.fire(result.results[0].alternatives[0].transcript)

		self.websocket.close()
		loop.stop()
		# loop.close()


	def getAuthenticationToken(self, hostname, serviceName, username, password):
		uri = hostname + "/authorization/api/v1/token?url=" + hostname + '/' + \
			  serviceName + "/api"
		uri = uri.replace("wss://", "https://")
		uri = uri.replace("ws://", "https://")
		# print(uri)
		resp = requests.get(uri, auth=(username, password), verify=False,
							headers={'Accept': 'application/json'}, timeout=(30, 30))
		print(resp.text)
		jsonObject = resp.json()
		return jsonObject['token']
