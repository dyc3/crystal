import requests

from crystal.actions import BaseAction
from crystal.actions.responses import ActionResponseType, ActionResponseBasic, ActionResponseQuery, ActionResponsePromptList
from crystal import feedback
import logging
log = logging.getLogger(__name__)

class ActionGithub(BaseAction):
	"""docstring for ActionGithub."""
	def __init__(self):
		super(ActionGithub, self).__init__()
		self.handled_classifier = "github"
		self.requires_updater = False

	@classmethod
	def parse(self, sentence):
		for word in sentence:
			if word.lemma_ == "notification":
				return "list-notif"
			if word.lemma_ == "repository":
				return "list-repos"
		return

	@classmethod
	def get_notifications(self):
		# TODO: handle the config in crystal.core, because this is stupid
		config = {}
		with open("config.txt", "r") as f:
			for line in f:
				spl = line.split("=")
				config[spl[0]] = spl[1]
		self.GITHUB_ACCESS_TOKEN = config["github_access_token"]

		resp = requests.get("https://api.github.com/notifications?access_token={}".format(self.GITHUB_ACCESS_TOKEN))
		if resp.status_code == 200:
			log.debug(resp)
			return resp.json()
		else:
			log.error(resp)
			log.error(resp.url)
			return None

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		command = self.parse(sentence)

		if command == "list-notif" or command == "count-notif":
			notifs = self.get_notifications()
			if notifs == None:
				return ActionResponseBasic(ActionResponseType.FAILURE, "failed to get github notifications")
			if len(notifs) == 0:
				return ActionResponseQuery("You have no GitHub notifications.")

			if command == "count-notif":
				return ActionResponseQuery("You have {} GitHub notifications.".format(len(notifs)))
			else:
				return ActionResponsePromptList("GitHub Notifications", notifs)
		elif command == "list-repos" or command == "count-repos":
			# TODO: list my Github repositories
			pass
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, "unknown command: {}".format(command))

def getAction():
	return ActionGithub()
