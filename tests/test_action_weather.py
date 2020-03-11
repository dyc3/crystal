import unittest
import datetime
import spacy
from crystal.actions import weather

nlp = None

class TestActionWeather(unittest.TestCase):
	"""docstring for TestActionWeather."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_parse(self):
		# query, expected result
		test_set = [
			("what's the weather", "current"),
			("how hot is it", "current"),
			("is it cold outside", "current"),
			("do I need a jacket", "current"),
		]
		action_weather = weather.ActionWeather()
		for test, expectedResult in test_set:
			with self.subTest():
				doc = nlp(test)
				sent = next(doc.sents)
				self.assertEqual(action_weather.parse(sent), expectedResult, test)

if __name__ == '__main__':
	unittest.main()
