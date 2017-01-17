from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import spacy

class CommandClassifier():
	"""docstring for CommandClassifier."""
	def __init__(self, nlp):
		super(CommandClassifier, self).__init__()
		self.nlp = nlp
		self.clf = LinearSVC()
		self.vectorizer = CountVectorizer(tokenizer=self._tokenizeText, ngram_range=(1,1))
		self.pipe = Pipeline([('vectorizer', self.vectorizer), ('clf', self.clf)])

	# A custom function to tokenize the text using spaCy and convert to lemmas
	def _tokenizeText(self, sample):

		# get the tokens using spaCy
		tokens = self.nlp(sample)

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
