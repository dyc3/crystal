from abc import ABCMeta
import abc
import os
import importlib

class BaseAction(metaclass=ABCMeta):
	"""docstring for BaseAction."""
	def __init__(self):
		super(BaseAction, self).__init__()
		self.handled_classifier = None

	@classmethod
	@abc.abstractmethod
	def run(self, doc):
		pass

def load_actions():
	action_modules_str = ["actions."+a for a in os.listdir("actions") if "." not in a and a != "__pycache__"]

	action_modules = {}
	for value in action_modules_str:
		module = importlib.import_module(name=value)
		module = importlib.reload(module)
		action = module.getAction()
		action_modules[action.handled_classifier] = action

	return action_modules
