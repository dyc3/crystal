from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests
from twisted.internet import ssl, reactor, defer
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
import threading
import audioop
from audio import get_flac_data, get_raw_data

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
			# print("Binary message received: {0} bytes".format(len(payload)))
			pass
		else:
			text = payload.decode('utf8')
			# print("Watson: Text received: {0}".format(text))
			result = json.loads(text)
			if 'error' not in result:
				if 'results' in result and len(result['results']) > 0:
					if not result['results'][0]['final']:
						WatsonSpeechRecognizer.singleton.onSpeech.fire(result['results'][0]['alternatives'][0]['transcript'])
					else:
						WatsonSpeechRecognizer.singleton.onFinish.fire(result['results'][0]['alternatives'][0]['transcript'])
				elif 'state' in result:
					# print("Watson: server state:", result['state'])
					pass
			else:
				print("Watson received error:", result['error'])

	def onClose(self, wasClean, code, reason):
		WatsonSpeechRecognizer.singleton.websocket = self
		print("Watson: WebSocket connection closed ({}): {}".format(code, reason))
		WatsonSpeechRecognizer.singleton.onWebsocketClose(wasClean, code, reason)

	@property
	def is_closed(self):
		d = defer.Deferred();
		def _errBack(err):
			print("is_closed ERR")
			print(err)
		d.addErrback(_errBack)
		def _getResult(client):
			# print("_getResult - results", client)
			return client.state == client.STATE_CLOSED
		d.addCallback(_getResult)
		return d;

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
		self.websocket_connector = None
		self.websocket = None

		if not WatsonSpeechRecognizer.singleton:
			WatsonSpeechRecognizer.singleton = self
		else:
			self = WatsonSpeechRecognizer.singleton

		def _onFinish(text):
			self.status = "not-speaking"
			self.websocket.sendMessage('{"action":"stop"}'.encode('utf8'), isBinary=False)
		self.onFinish += _onFinish

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
			self._speakingBuffer = [] # array of frames to be sent if we are actually speaking
			self.threadReceiver.start()

	def Stop(self):
		if self.isRunning:
			print("STOPPING")
			self.isRunning = False
			self.threadReceiver.join()
			self.websocket.close()

	def GiveFrame(self, frame, sample_rate, sample_width, power_threshold=300):
		def doSendFrame(frame, sample_rate, sample_width):
			raw_data = get_raw_data(frame, sample_rate, sample_width)
			if len(raw_data) > 0:
				self.websocket.sendMessage(raw_data, isBinary=True)

		if self.websocket == None or self.websocket.state != WatsonSpeechClientProtocol.STATE_OPEN:
			# print("\nno websocket")
			return

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
			self.websocket.sendMessage('{"action":"start", "content-type":"audio/l16;rate=16000;channels=2;", "interim_results":true}'.encode('utf8'), isBinary=False)
			if len(self._speakingBuffer) > 0:
				for f in self._speakingBuffer:
					doSendFrame(f, sample_rate, sample_width)
				self._speakingBuffer = []

		if self.status == "speaking":
			doSendFrame(frame, sample_rate, sample_width)
			if frame_power >= power_threshold:
				self._notSpeakingTicks = 0
			else:
				self._notSpeakingTicks += 1

		if self._notSpeakingTicks >= 10:
			self.status = "not-speaking"
			self.websocket.sendMessage('{"action":"stop"}'.encode('utf8'), isBinary=False)

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

	# doesn't work in current state
	def onWebsocketClose(self, wasClean, code, reason):
		reactor.stop()
		self.websocket = None
		print("waiting for reactor to stop...")
		while reactor.running:
			# print(".", end='')
			pass
		reactor.run()
