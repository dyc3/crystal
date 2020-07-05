from enum import Enum
from abc import ABCMeta
import rofi

class ActionResponseType(Enum):
	UNKNOWN = None
	SUCCESS = 0
	FAILURE = 1
	REQUEST_INFO = 2 # Request more info from the user

class ActionResponseBase(metaclass=ABCMeta):
	def __init__(self):
		self.name = "ActionResponseBase"
		self.type = ActionResponseType.UNKNOWN

class ActionResponseBasic(ActionResponseBase):
	def __init__(self, response_type, message=""):
		super(ActionResponseBasic, self).__init__()
		self.name = "ActionResponseBasic"
		self.type = response_type
		self.message = message

class ActionResponseQuery(ActionResponseBase):
	"""
	To be used when Crystal needs to respond to a direct query.
	For example: "What is the time?"
	"""
	def __init__(self, message):
		super(ActionResponseQuery, self).__init__()
		self.name = "ActionResponseQuery"
		self.type = ActionResponseType.SUCCESS
		self.message = message

class ActionResponseQueryList(ActionResponseBase):
	def __init__(self, prompt, items):
		super(ActionResponseQueryList, self).__init__()
		self.name = "ActionResponseQueryList"
		self.type = ActionResponseType.SUCCESS
		self.prompt = prompt # the query to prompt the user with
		self.items = items

class ActionResponsePromptList(ActionResponseQueryList):
	def __init__(self, prompt, items):
		super(ActionResponsePromptList, self).__init__(prompt, items)
		self.name = "ActionResponsePromptList"
		self.type = ActionResponseType.REQUEST_INFO

def show_user_prompt(action_response: ActionResponseQueryList):
	assert isinstance(action_response, ActionResponseQueryList)

	rofi_prompt = rofi.Rofi(len(action_response.items))
	rofi_result = rofi_prompt.select(action_response.prompt, action_response.items)
	return rofi_result