import os
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
import spacy

import logging
log = logging.getLogger(__name__)

def load_nlp(model: str):
	"""
	model: specify spaCy model to use
	"""
	global nlp
	log.debug("spaCy using GPU: {}".format(spacy.prefer_gpu()))
	try:
		nlp = spacy.load(model)
	except OSError:
		# model loading failed, it probably doesn't exist
		# download it
		os.system("python -m spacy download {}".format(model))
		nlp = spacy.load(model)

def parse_nlp(text: str):
	return nlp(text)

def get_stop_words():
	return nlp.Defaults.stop_words

class CommandClassifier():
	"""docstring for CommandClassifier."""
	def __init__(self):
		super(CommandClassifier, self).__init__()
		self.clf = CalibratedClassifierCV(LinearSVC())
		self.vectorizer = CountVectorizer(tokenizer=self._tokenizeText, ngram_range=(1,1))
		self.pipe = Pipeline([('vectorizer', self.vectorizer), ('clf', self.clf)])

	# A custom function to tokenize the text using spaCy and convert to lemmas
	def _tokenizeText(self, sample):

		# get the tokens using spaCy
		tokens = parse_nlp(sample)

		# lemmatize
		lemmas = []
		for tok in tokens:
			lemmas.append(tok.lemma_.lower().strip() if tok.lemma_ != "-PRON-" else tok.lower_)
		# remove stop words
		stop_words = get_stop_words()
		tokens = [word for word in lemmas if word not in stop_words]

		# remove large strings of whitespace
		while "" in tokens:
			tokens.remove("")
		while " " in tokens:
			tokens.remove(" ")
		while "\n" in tokens:
			tokens.remove("\n")
		while "\n\n" in tokens:
			tokens.remove("\n\n")

		return tokens

	def fit(self, X, y):
		self.pipe.fit(X, y)

	def predict(self, X):
		"""
		Takes array of string samples `X` and returns an array of tuples that correspond to the input samples (classification, confidence)
		"""
		result = []
		pred = self.pipe.predict(X)
		pred_proba = self.pipe.predict_proba(X)
		for class_, prob in zip(pred, pred_proba):
			idx = np.where(self.clf.classes_ == class_)
			result += [(class_, float(prob[idx]))]
		return result
