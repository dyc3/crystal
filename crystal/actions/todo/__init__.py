import todoist.api

from crystal.actions import BaseAction
from crystal.actions.responses import ActionResponseType, ActionResponseBasic, ActionResponseQuery, ActionResponsePromptList
from crystal import feedback
import logging
log = logging.getLogger(__name__)

class ActionTodo(BaseAction):
	"""docstring for ActionTodo."""
	def __init__(self):
		super(ActionTodo, self).__init__()
		self.handled_classifier = "todo"
		self.requires_updater = False

	@classmethod
	def log_in(self):
		# TODO: handle the config in crystal.core, because this is stupid
		config = {}
		with open("config.txt", "r") as f:
			for line in f:
				spl = line.split("=")
				config[spl[0]] = spl[1]
		self.TODOIST_ACCESS_TOKEN = config["todoist_access_token"]
		self.TODOIST_CLIENT_ID = config["todoist_client_id"]
		self.TODOIST_CLIENT_SECRET = config["todoist_client_secret"]

		self.todo_api = todoist.api.TodoistAPI(token=self.TODOIST_ACCESS_TOKEN)

	@classmethod
	def parse(self, sentence):
		for word in sentence:
			if word.lemma_ in ["what", "read"]:
				return "list"
			if word.lemma_ == ["add"]:
				return "add"
		return

	@classmethod
	def get_todo_list_state(self):
		self.log_in()

		self.todo_api.sync_token = "*"
		current_state = self.todo_api.sync()
		return current_state

	@classmethod
	def get_all_todo_items(self, todoist_state):
		self.log_in()

		items = []
		for p in todoist_state["projects"]:
			if p["name"] not in ["Inbox", "Personal", "Work"]:
				continue

			log.debug("collecting from {}".format(p["name"]))
			for i in todoist_state["items"]:
				if i["project_id"] == p["id"]:
					items.append(i["content"])
		return items

	@classmethod
	def run(self, doc):
		sentence = next(doc.sents)
		command = self.parse(sentence)

		log.info("Grabbing state...")
		todo_state = self.get_todo_list_state()
		log.debug(todo_state)

		if command == "list":
			log.info("Collecting all items...")
			todo_items = self.get_all_todo_items(todo_state)

			response = ActionResponsePromptList("Todo list", todo_items)
			response.type = ActionResponseType.SUCCESS
			return response

		if command == "add":
			return ActionResponseBasic(ActionResponseType.FAILURE, "Can't do that yet")

def getAction():
	return ActionTodo()
