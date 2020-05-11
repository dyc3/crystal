import todoist.api

from crystal.actions import BaseAction
from crystal.actions.responses import ActionResponseType, ActionResponseBasic, ActionResponseQuery, ActionResponsePromptList
from crystal import core, feedback
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
		self.TODOIST_ACCESS_TOKEN = core.get_config("todoist_access_token")
		self.TODOIST_CLIENT_ID = core.get_config("todoist_client_id")
		self.TODOIST_CLIENT_SECRET = core.get_config("todoist_client_secret")

		self.todo_api = todoist.api.TodoistAPI(token=self.TODOIST_ACCESS_TOKEN)

	@classmethod
	def parse(self, doc):
		for word in doc:
			if word.lemma_ in ["what", "read", "get", "show"]:
				return "list"
			if word.lemma_ in ["add", "put"]:
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
		command = self.parse(doc)

		log.info("Grabbing state...")
		todo_state = self.get_todo_list_state()
		log.debug(todo_state)

		if command == "list":
			log.info("Collecting all items...")
			todo_items = self.get_all_todo_items(todo_state)

			response = ActionResponsePromptList("Todo list", todo_items)
			response.type = ActionResponseType.SUCCESS
			return response
		elif command == "add":
			return ActionResponseBasic(ActionResponseType.FAILURE, "Can't do that yet")
		else:
			log.error(f"Unknown command: {command}")
			return ActionResponseBasic(ActionResponseType.FAILURE, "Unknown command: {command}")

def getAction():
	return ActionTodo()
