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
			if word.lemma_ in ["click", "move", "press", "scroll"]:
				inputaction = word.lemma_
				break
			if word.lemma_ in ["type", "dictate"]:
				inputaction = "type"
				break

		# default parameters
		click_param = "left"
		scroll_direction = "down"
		scroll_amount = 0
		move_direction = ""
		move_amount = 0
		press_param = ""
		type_param = ""

		# extract the parameters
		if inputaction == "click":
			word = utils.find_word(sentence.doc, ["left","middle","right","double","triple"])
			if word:
				click_param = word.lemma_

		elif inputaction == "scroll":
			for word in sentence:
				if str(word) in ["up", "down"]:
					scroll_direction = word.lemma_
					scroll_amount = 8
				elif str(word) in ["top", "bottom"]:
					scroll_direction = {"top":"up", "bottom":"down"}[str(word)]
					scroll_amount = 1000

		elif inputaction == "move":
			unit_size = 10
			for word in sentence:
				numToken = None
				if str(word) in ["up", "down", "left", "right", "center"]:
					move_direction = str(word)
				elif word.dep_ == "prep":
					if str(word) == "by":
						for prepchild in word.children:
							if prepchild.dep_ == "pobj":
								if prepchild.lemma_ in ["pixel", "unit"]:
									if prepchild.lemma_ == "pixel":
										unit_size = 1
									for c in prepchild.children:
										if c.like_num:
											numToken = c
								elif prepchild.like_num:
									numToken = prepchild
				elif word.lemma_ in ["pixel", "unit"]:
					if word.lemma_ == "pixel":
						unit_size = 1
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
			move_amount *= unit_size

		elif inputaction == "press":
			word = utils.find_word(sentence.doc, ["press"])
			if word and word.nbor(1):
				press_param = '+'.join(map(str, sentence.doc[word.i + 1:]))

		elif inputaction == "type":
			word = utils.find_word(sentence.doc, ["type", "dictate"])
			if word and word.nbor(1):
				type_param = ' '.join(map(str, sentence.doc[word.i + 1:]))

		if inputaction == "click":
			return inputaction, (click_param,)
		elif inputaction == "scroll":
			return inputaction, (scroll_direction, scroll_amount,)
		elif inputaction == "move":
			return inputaction, (move_direction, move_amount)
		elif inputaction == "press":
			return inputaction, (press_param,)
		elif inputaction == "type":
			return inputaction, (type_param,)

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
				pyautogui.typewrite(parameters[0], interval=(0.05/len(parameters[0])))
			else:
				log.warn("human-input: No text specified")
		elif inputaction == "press":
			if parameters:
				pyautogui.press(parameters)
			else:
				log.warn("human-input: No key specified")
		elif inputaction == "scroll":
			scroll_direction, scroll_amount = parameters
			if scroll_direction == "down":
				scroll_amount *= -1
			# positive number is up, negative number is down
			pyautogui.scroll(scroll_amount)
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
