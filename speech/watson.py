from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
from twisted.internet import ssl, reactor
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
import threading
import audioop

class WatsonSpeechClientProtocol(WebSocketClientProtocol):
	def __init__(self):
		# super(WebSocketClientFactory, self).__init__()
		WatsonSpeechRecognizer.singleton.websocket = self

	def onConnect(self, response):
		WatsonSpeechRecognizer.singleton.websocket = self
		print("Watson: Server connected: {0}".format(response.peer))

	def onOpen(self):
		WatsonSpeechRecognizer.singleton.websocket = self
		print("Watson: WebSocket connection open.")

	def onMessage(self, payload, isBinary):
		WatsonSpeechRecognizer.singleton.websocket = self
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			text = payload.decode('utf8')
			print("Watson: Text received: {0}".format(text))
			result = json.loads(text)
			if not result['results'][0]['final']:
				self.onSpeech.fire(result['results'][0]['alternatives'][0]['transcript'])
			else:
				self.onFinish.fire(result['results'][0]['alternatives'][0]['transcript'])

	def onClose(self, wasClean, code, reason):
		WatsonSpeechRecognizer.singleton.websocket = self
		print("Watson: WebSocket connection closed: {0}".format(reason))

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

		self.websocket_factory = WebSocketClientFactory("wss://"+ self.hostname +"/speech-to-text/api/v1/recognize")
		self.websocket_factory.protocol = WatsonSpeechClientProtocol
		self.websocket = None

		if not WatsonSpeechRecognizer.singleton:
			WatsonSpeechRecognizer.singleton = self
		else:
			self = WatsonSpeechRecognizer.singleton

	def Start(self):
		print("Watson: isRunning =", self.isRunning)
		if not self.isRunning:
			headers = {}
			print("Watson: getting token...")
			headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://"+ self.hostname,"speech-to-text",self.username,self.password)
			self.websocket_factory.headers = headers

			print("Watson: connecting...")
			if self.websocket_factory.isSecure:
				contextFactory = ssl.ClientContextFactory()
			else:
				contextFactory = None
			self.websocket_connector = connectWS(self.websocket_factory, contextFactory=contextFactory)
			# self.websocket_connector.recognizer = self
			print("Watson: connected")

			self.threadReceiver = threading.Thread(name="watson-speech-client")
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
			self.websocket.close()

	def GiveFrame(self, frame, power_threshold=300):
		if self.websocket == None:
			print("\nno websocket")
			return

		frame_power = audioop.rms(frame, 2)
		if self.status == "not-speaking" and frame_power >= power_threshold:
			self.status = "speaking"
			self._notSpeakingTicks = 0
			self.websocket.sendMessage('{action:"start", content-type="audio/flac"}'.encode('utf8'), isBinary=False)

		if self.status == "speaking":
			self.websocket.sendMessage(frame, isBinary=True)
			if frame_power >= power_threshold:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 50:
			self.status = "not-speaking"
			self.websocket.sendMessage('{action:"stop"}'.encode('utf8'), isBinary=False)

	def _doThreadReceiver(self):
		reactor.run()

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
