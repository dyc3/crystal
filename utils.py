# TODO: move to crystal.core

import os
from timeit import default_timer as timer
import logging
log = logging.getLogger(__name__)

def text2int(textnum, numwords={}):
	if not numwords:
		units = [
			"zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
			"nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
			"sixteen", "seventeen", "eighteen", "nineteen",
		]

		tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

		scales = ["hundred", "thousand", "million", "billion", "trillion"]

		numwords["and"] = (1, 0)
		for idx, word in enumerate(units):	numwords[word] = (1, idx)
		for idx, word in enumerate(tens):	 numwords[word] = (1, idx * 10)
		for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

	if textnum == "a":
		return 1

	current = result = 0
	for word in textnum.split():
		if word not in numwords:
			raise Exception("Illegal word: " + word)

		scale, increment = numwords[word]
		current = current * scale + increment
		if scale > 100:
			result += current
			current = 0

	return result + current

def runAndPrint(command):
	"""
	returns the command's exit code
	"""
	log.info("Running {0}...".format(command))
	return os.system(command)

def printSpacy(sentence):
	for token in sentence:
		print(token, token.pos_, token.dep_, "parent:", token.head)

def find_word(doc, words, min_idx=0):
	"""
	Takes a spaCy doc, and `words`, a list of strings.
	Returns the first token in `doc` that matches any of the words or their lemma_
	"""
	if isinstance(words, str):
		words = [words]
	assert isinstance(words, list) and len(words) > 0

	for token in doc:
		if token.i < min_idx:
			continue
		for word in words:
			if token.text.lower() == word or token.lemma_ == word:
				return token
	return None

def parse_duration_to_seconds(tokens):
	"""
	TODO: implement this
	Takes a spacy span of tokens that represent a span of time.
	Returns the duration of the time span in seconds.
	"""
	pass

class ExecutionTimer():
	def __init__(self, log, name="Timer"):
		self.name = name
		self.log = log

	def __enter__(self):
		self.start = timer()

	def __exit__(self, type, value, traceback):
		end = timer()
		self.log.debug(f"{self.name} took {end - self.start:.4f} seconds")
