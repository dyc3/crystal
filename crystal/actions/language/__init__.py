import crystal.core
from crystal.actions import BaseAction
from crystal.actions.responses import *
import utils
import requests

DICTIONARY_API_URL = "https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key={}" # target_word, api_key

class ActionLanguage(BaseAction):
	"""Handles user queries related to language, like spelling and definitions."""
	def __init__(self):
		super(ActionLanguage, self).__init__()
		self.handled_classifier = "language"
		self.requires_updater = False

	@classmethod
	def parse_api_response_definition(self, resp_json: dict) -> str:
		"""
		Extracts the definition out of the json returned by the API.
		"""
		def_block = resp_json[0]["shortdef"]
		result = ""
		for i, d in enumerate(def_block):
			result += "{}. {}\n".format(i, d)
		return result

	@classmethod
	def get_definition(self, word: str) -> str:
		"""
		Gets the definition of the specified `word`.
		Returns a string.
		"""
		dictionary_api_key = crystal.core.get_config("webster_dictionary_api_key")
		if not dictionary_api_key:
			raise Exception("No Webster Dictionary API Key found")
		resp = requests.get(DICTIONARY_API_URL.format(word, dictionary_api_key))
		resp.raise_for_status()
		return self.parse_api_response_definition(resp.json())

	@classmethod
	def parse(self, doc) -> tuple:
		"""
		Returns a tuple of 2 strings: (command, target word)
		"""
		word = utils.find_word(doc, "spell")
		if word and word.nbor(1):
			return "spell", word.nbor(1).text

		word = utils.find_word(doc, "define")
		if word and word.nbor(1):
			return "define", word.nbor(1).text

		word = utils.find_word(doc, ["definition", "spelling"])
		if word and word.nbor(2):
			if word.text == "spelling":
				command = "spell"
			else:
				command = "define"

			if word.nbor(1).text == "of":
				return command, word.nbor(2).text
			else:
				return command, word.nbor(1).text

		return None, None

	@classmethod
	def run(self, doc):
		dictionary_api_key = crystal.core.get_config("webster_dictionary_api_key")
		if not dictionary_api_key:
			return ActionResponseBasic(ActionResponseType.FAILURE, "No webster_dictionary_api_key found in config")

		command, target_word = self.parse(doc)
		if command == "spell":
			return ActionResponseQuery(" ".join(i for i in target_word.upper()))
		if command == "define":
			definition = self.get_definition(target_word)
			return ActionResponseQuery(definition)

		return ActionResponseBasic(ActionResponseType.FAILURE, "Unknown command: {}".format(command))

def getAction():
	return ActionLanguage()
