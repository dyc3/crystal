import requests
import datetime

from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import core, feedback
import logging
log = logging.getLogger(__name__)

class ActionGithub(BaseAction):
	"""docstring for ActionGithub."""
	def __init__(self):
		super(ActionGithub, self).__init__()
		self.handled_classifier = "github"
		self.requires_updater = True
		self.init()

	@classmethod
	def init(self):
		self.GITHUB_ACCESS_TOKEN = core.get_config("github_access_token")
		if not self.GITHUB_ACCESS_TOKEN:
			log.warn("No github_access_token found in config!")
		self.last_notif_check = datetime.datetime.now()
		self.last_notif_count = 0

	@classmethod
	def parse(self, doc):
		cmd_type = "" # list, count
		cmd_target = "" # notif, repos
		for word in doc:
			if word.lemma_ in ["list", "show", "check"]:
				cmd_type = "list"
			elif word.lemma_ in ["count"]:
				cmd_type = "count"
			elif word.lemma_ == "how" and word.nbor(1).lemma_ == "many":
				cmd_type = "count"
			elif word.lemma_ == "any" and (word.nbor(-2).lemma_ == "be" or word.nbor(-1).lemma_ == "have"):
				# the lemma_ property of the word "are" is "be"
				cmd_type = "count"

			if word.lemma_ in ["notification", "check"]:
				cmd_target = "notif"
			elif word.lemma_ == "repository":
				cmd_target = "repos"
		if cmd_type and cmd_target:
			return "{}-{}".format(cmd_type, cmd_target)
		if not cmd_type:
			log.warn("Unable to determine command type")
		if not cmd_type:
			log.warn("Unable to determine command target")
		return None

	@classmethod
	def get_notifications(self):
		try:
			resp = requests.get("https://api.github.com/notifications", auth=("dyc3", self.GITHUB_ACCESS_TOKEN))
			if resp.status_code == 200:
				log.debug(resp)
				return resp.json()
			else:
				log.error(resp)
				log.error(resp.url)
				return None
		except requests.exceptions.Timeout:
			log.warn("Timed out when getting notifications")
			return None

	@classmethod
	def run(self, doc):
		command = self.parse(doc)

		if command == "list-notif" or command == "count-notif":
			notifs = self.get_notifications()
			if notifs == None:
				return ActionResponseBasic(ActionResponseType.FAILURE, "failed to get github notifications")
			if len(notifs) == 0:
				return ActionResponseQuery("You have no GitHub notifications.")

			if command == "count-notif":
				return ActionResponseQuery("You have {} GitHub notifications.".format(len(notifs)))
			else:
				resp = ActionResponseQueryList("GitHub Notifications", notifs)
				resp.type = ActionResponseType.SUCCESS
				return resp
		elif command == "list-repos" or command == "count-repos":
			# TODO: list my Github repositories
			return ActionResponseBasic(ActionResponseType.FAILURE, "Can't do that yet: {}".format(command))
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, "unknown command: {}".format(command))

	@classmethod
	def update(self):
		delta = datetime.datetime.now() - self.last_notif_check
		if delta.total_seconds() >= 60:
			self.last_notif_check = datetime.datetime.now()

			notif_count = len(self.get_notifications())
			if notif_count != self.last_notif_count and notif_count > 0:
				feedback.ShowNotify(f"You have {notif_count} GitHub notifications")
			self.last_notif_count = notif_count

def getAction():
	return ActionGithub()
