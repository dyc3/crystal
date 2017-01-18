from eventhook import EventHook
from speech.base import BaseSpeechRecognizer
import json
import requests

class WatsonSpeechRecognizer(BaseSpeechRecognizer):
	"""docstring for WatsonSpeechRecognizer."""
	def __init__(self, username, password):
		super(BaseSpeechRecognizer, self).__init__()
		self.onSpeech = EventHook() # called while speaking, but not finished with request (only usable with speech streaming)
		self.onFinish = EventHook() # called when speaking is finished

		self.username = username
		self.password = password

	def Start():
		headers = {}
		headers['X-Watson-Authorization-Token'] = self.getAuthenticationToken("wss://stream.watsonplatform.net","speech-to-text",self.username,self.password)
		self.websocket = websockets.connect("wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize",extra_headers=headers)

	def Stop():
		pass


	def onOpen():
		pass

	def onMessage():
		pass

	def onClose():
		pass


	def getAuthenticationToken(hostname, serviceName, username, password):
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
