from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import feedback
import utils
import pyautogui
import logging
log = logging.getLogger(__name__)

class ActionHumanInput(BaseAction):
	"""docstring for ActionHumanInput."""
	def __init__(self):
		super(ActionHumanInput, self).__init__()
		self.handled_classifier = "human-input"
		self.requires_updater = False

	@classmethod
	def extract_parameters(self, doc):
		"""
		Extracts action and parameters for human_input

		Returns a tuple, a string of the action and a tuple of the parameters.
		"""
		sentence = next(doc.sents)

		inputaction = None

		# extract the action
		for word in sentence:
			if word.lemma_ in ["click", "move", "type", "press", "scroll"]:
				inputaction = word.lemma_
				break

		# default parameters
		click_param = "left"
		scroll_direction = "down"
		scroll_amount = 0
		move_direction = ""
		move_amount = 0

		# extract the parameters
		for word in sentence:
			if inputaction == "click":
				if word.lemma_ in ["left","middle","right","double","triple"]:
					click_param = word.lemma_
					break

			elif inputaction == "scroll":
				if word.lemma_ in ["up", "down"]:
					scroll_direction = word.lemma_
					scroll_amount = 8
				elif word.lemma_ in ["top", "bottom"]:
					scroll_direction = {"top":"up", "bottom":"down"}[word.lemma_]
					scroll_amount = 10000
				break

			elif inputaction == "move":
				numToken = None
				if str(word) in ["up", "down", "left", "right", "center"]:
					move_direction = str(word)
				elif word.dep_ == "prep":
					if str(word) == "by":
						for prepchild in word.children:
							if prepchild.dep_ == "pobj":
								if prepchild.lemma_ == "pixel":
									for c in prepchild.children:
										if c.like_num:
											numToken = c
								elif prepchild.like_num:
									numToken = prepchild
				elif word.lemma_ == "pixel":
					for c in word.children:
						if c.like_num:
							numToken = c
				elif word.like_num:
					numToken = word
				if numToken:
					try:
						move_amount = int(str(numToken))
					except:
						try:
							move_amount = utils.text2int(str(numToken))
						except Exception as e:
							log.error("could not parse {}".format(numToken))
							break


		if inputaction == "click":
			return inputaction, (click_param,)
		elif inputaction == "scroll":
			return inputaction, (scroll_direction, scroll_amount,)
		elif inputaction == "move":
			return inputaction, (move_direction, move_amount)

	@classmethod
	def run(self, doc):
		inputaction, inputparameters = self.extract_parameters(doc)
		if inputaction:
			self.human_input(inputaction, parameters=inputparameters)
			return ActionResponseBasic(ActionResponseType.SUCCESS)
		else:
			print("inputaction can't be None")

	@classmethod
	def human_input(self, inputaction, parameters=None):
		log.info("human-input: {} ({})".format(inputaction, parameters))
		assert inputaction != None, "human-input: inputaction can't be None"

		if inputaction == "click":
			if parameters[0] in ["left","middle","right"]:
				pyautogui.click(button=parameters[0])
			elif parameters[0] == "double":
				pyautogui.doubleClick()
			elif parameters[0] == "triple":
				pyautogui.tripleClick()
		elif inputaction == "type":
			if parameters:
				pyautogui.typewrite(parameters[0], interval=(0.2/len(parameters)))
			else:
				log.warn("human-input: No text specified")
		elif inputaction == "press":
			if parameters:
				pyautogui.press(parameters)
			else:
				log.warn("human-input: No key specified")
		elif inputaction == "scroll":
			genericScroll = 8
			superScroll = 100
			# positive number is up, negative number is down
			if "up" in parameters:
				pyautogui.scroll(genericScroll)
			elif "down" in parameters:
				pyautogui.scroll(-genericScroll)
			elif "top" in parameters:
				pyautogui.scroll(superScroll)
			elif "bottom" in parameters:
				pyautogui.scroll(-superScroll)
			else:
				log.warn("human-input: scrolling in that direction is not supported.")
		elif inputaction == "move":
			mouseact = None
			value = None
			for p in parameters:
				if p == None or p == "":
					continue
				if p in ["up","down","left","right","set","center"]:
					mouseact = p
				else:
					value = int(p)
			if mouseact != None:
				if mouseact in ["up","down","left","right"]:
					x = value if mouseact == "right" else (-value if mouseact == "left" else None)
					y = value if mouseact == "down" else (-value if mouseact == "up"  else None)
					pyautogui.moveRel(x, y, duration=0.25, tween=pyautogui.easeInOutQuad)
				elif mouseact == "center":
					screenWidth, screenHeight = pyautogui.size()
					x, y = pyautogui.center((0,0,screenWidth,screenHeight))
					pyautogui.moveTo(x, y, duration=0.25, tween=pyautogui.easeInOutQuad)
				else:
					log.warn("can't move the mouse like that")
			else:
				log.warn("can't move the mouse like that")
		else:
			log.error("human-input: inputaction {} not yet supported".format(inputaction))

def getAction():
	return ActionHumanInput()
