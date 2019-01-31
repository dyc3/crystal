import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
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

class CommandClassifier():
	"""docstring for CommandClassifier."""
	def __init__(self):
		super(CommandClassifier, self).__init__()
		self.clf = LinearSVC()
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
		tokens = lemmas

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
		self.pipe.fit(X, y);

	def predict(self, X):
		return self.pipe.predict(X)
