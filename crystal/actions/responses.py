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
		self.type = ActionResponseType.UNKNOWN

class ActionResponseBasic(ActionResponseBase):
	def __init__(self, response_type, message=""):
		super(ActionResponseBasic, self).__init__()
		self.type = response_type
		self.message = message

class ActionResponseQuery(ActionResponseBase):
	"""
	To be used when Crystal needs to respond to a direct query.
	For example: "What is the time?"
	"""
	def __init__(self, message):
		super(ActionResponseQuery, self).__init__()
		self.type = ActionResponseType.SUCCESS
		self.message = message

class ActionResponsePromptList(ActionResponseBase):
	def __init__(self, prompt, items):
		super(ActionResponsePromptList, self).__init__()
		self.type = ActionResponseType.REQUEST_INFO
		self.prompt = prompt # the query to prompt the user with
		self.items = items

def show_user_prompt(action_response: ActionResponsePromptList):
	assert isinstance(action_response, ActionResponsePromptList)

	rofi_prompt = rofi.Rofi(action_response.items)
	rofi_result = rofi_prompt.select(action_response.prompt, action_response.items)
	return rofi_result