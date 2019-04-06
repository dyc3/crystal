from crystal.actions import BaseAction
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
		sentence = next(doc.sents)

		inputaction = None
		inputparameters = None
		# JANKY: bug in spaCy prevents this from being parsed correctly
		if str(sentence) == "left click":
			inputaction = "click"
			inputparameters = "left"

		if str(sentence.root).lower() in ["click", "move", "type", "press", "scroll"]:
			if inputaction == None:
				inputaction = str(sentence.root).lower()
		for child in sentence.root.children:
			if inputaction == "click":
				if child.dep_ == "amod" and str(child).lower() in ["left","middle","right","double","triple"]:
					inputparameters = str(child).lower()
			elif inputaction == "scroll":
				if child.dep_ == "prep" and str(child) == "to":
					for prepchild in child.children:
						if prepchild.dep_ == "pobj" and str(prepchild) in ["top", "bottom"]:
							inputparameters = str(prepchild).lower()
				elif str(child) in ["up","down","left","right"]:
					if inputparameters == None:
						inputparameters = str(child).lower()
			elif inputaction == "move":
				numToken = None
				num = None
				if str(child) in ["up","down","left","right"]:
					s = "{} ".format(str(child).lower())
					if inputparameters == None:
						inputparameters = s
					else:
						inputparameters += s
				elif child.dep_ == "prep":
					if str(child) == "by":
						for prepchild in child.children:
							if prepchild.dep_ == "pobj":
								if prepchild.lemma_ == "pixel":
									for c in prepchild.children:
										if c.like_num:
											numToken = c
								elif prepchild.like_num:
									numToken = prepchild
					elif str(child) == "to":
						for prepchild in child.children:
							if prepchild.dep_ == "pobj":
								if str(prepchild) in ["left","right","center"]:
									s = "{} ".format(str(prepchild).lower())
									if inputparameters == None:
										inputparameters = s
									else:
										inputparameters += s
				elif child.lemma_ == "pixel":
					for c in child.children:
						if c.like_num:
							numToken = c
				elif child.like_num:
					numToken = child
				if numToken != None:
					try:
						num = int(str(numToken))
					except:
						try:
							num = utils.text2int(str(numToken))
						except Exception as e:
							print("could not parse {}".format(numToken))
							break
				if num != None:
					s = "{} ".format(num)
					if inputparameters == None:
						inputparameters = s
					else:
						inputparameters += s
		if inputparameters != None:
			inputparameters = inputparameters.rstrip()
		return inputaction, inputparameters

	@classmethod
	def run(self, doc):
		inputaction, inputparameters = self.extract_parameters(doc)
		if inputaction != None:
			self.human_input(inputaction, parameters=inputparameters)
		else:
			print("inputaction can't be None")

	@classmethod
	def human_input(self, inputaction, parameters=None):
		log.info("human-input: {} ({})".format(inputaction, parameters))
		assert inputaction != None, "human-input: inputaction can't be None"

		if inputaction == "click" and parameters == None:
			parameters = "left"

		if inputaction == "click":
			if parameters in ["left","middle","right"]:
				pyautogui.click(button=parameters)
			elif parameters == "double":
				pyautogui.doubleClick()
			elif parameters == "triple":
				pyautogui.tripleClick()
		elif inputaction == "type":
			if parameters != None:
				pyautogui.typewrite(parameters, interval=(0.2/len(parameters)))
			else:
				log.warn("human-input: No text specified")
		elif inputaction == "press":
			if parameters != None:
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
			for p in parameters.split(' '):
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
