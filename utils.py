# TODO: move to crystal.core

import os
from timeit import default_timer as timer
import numpy as np
import re
import logging
log = logging.getLogger(__name__)

def text2int(textnum, numwords={}):
	match_literals = re.search(r"\d+", textnum)
	if match_literals:
		return int(match_literals[0])

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

def ordinal_to_int(text):
	text = text.strip(",. ")
	match_literals = re.search(r"\d+", text)
	if match_literals:
		return int(match_literals[0])
	numwords = ["first", "second", "third"]
	if text in numwords:
		return numwords.index(text) + 1
	elif text.endswith("th"):
		return text2int(text[:-2])

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

def is_num_word(token):
	"""
	Check if a token could be a part of a number in word form
	"""
	return (token.like_num or token.text in ["and", "point"]) and not token.is_digit

def select_number_bleedy(token):
	"""
	Takes a token, and grabs the adjacent tokens that are numbers in word form.
	"""
	start_idx = token.i
	end_idx = token.i
	while start_idx > 0 and is_num_word(token.doc[start_idx - 1]):
		start_idx -= 1
	while end_idx + 1 < len(token.doc) and is_num_word(token.doc[end_idx + 1]):
		end_idx += 1
	return token.doc[start_idx:end_idx + 1]

def parse_duration_to_seconds(tokens):
	"""
	Takes a spacy span of tokens that represent a span of time.
	Returns the duration of the time span in seconds.
	"""
	result = 0
	hours = find_word(tokens, "hour")
	if hours: result += text2int(select_number_bleedy(hours.nbor(-1)).text) * 60 * 60
	minutes = find_word(tokens, "minute")
	if minutes: result += text2int(select_number_bleedy(minutes.nbor(-1)).text) * 60
	seconds = find_word(tokens, "second")
	if seconds: result += text2int(select_number_bleedy(seconds.nbor(-1)).text)
	return result

def levenshtein(seq1, seq2):
	size_x = len(seq1) + 1
	size_y = len(seq2) + 1
	matrix = np.zeros((size_x, size_y))
	for x in range(size_x):
		matrix[x, 0] = x
	for y in range(size_y):
		matrix[0, y] = y

	for x in range(1, size_x):
		for y in range(1, size_y):
			matrix[x,y] = min(
				matrix[x-1, y] + 1,
				matrix[x-1, y-1] + (0 if seq1[x-1] == seq2[y-1] else 1),
				matrix[x, y-1] + 1
			)
	return matrix[size_x - 1, size_y - 1]

class ExecutionTimer():
	def __init__(self, log, name="Timer"):
		self.name = name
		self.log = log

	def __enter__(self):
		self.start = timer()

	def __exit__(self, type, value, traceback):
		end = timer()
		self.log.debug(f"{self.name} took {end - self.start:.4f} seconds")
