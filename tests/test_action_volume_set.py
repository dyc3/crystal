import unittest
import spacy
from crystal.actions import volume_set
from hypothesis import given, example
import hypothesis.strategies as st
import inflect

nlp = None
p = inflect.engine()

class TestActionVolumeSet(unittest.TestCase):
	"""docstring for TestActionVolumeSet."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en_core_web_sm")

	def test_action_volume_set(self):
		# current_volume, query string, expected result
		test_set = [
			(0.5, "set volume to 80%", 0.8),
			(0.5, "set volume to 20 percent", 0.2),
			(0.5, "set volume to 40", 0.4),
			(0.5, "turn it up to 70", 0.7),
			(0.5, "turn it down to 20", 0.2),
			(0.5, "put volume at 40", 0.4),
			(0.5, "put the volume at 60", 0.6),
			(0.5, "put the volume to 75", 0.75),
			(0.3, "crystal volume 50%", 0.5),
			(0.3, "crystal volume 50 percent", 0.5),
			(0.3, "crystal volume 60", 0.6),

			(0.5, "increase volume", 0.6),
			(0.5, "increase the volume", 0.6),
			(0.5, "increase volume by 40", 0.9),
			(0.5, "turn up the volume", 0.6),
			(0.5, "turn it up by 30", 0.8),
			(0.5, "Turn It Up by 20%", 0.7),
			(0.5, "volume up", 0.6),
			(0.5, "turn the volume up", 0.6),
			(0.5, "turn the volume up by twenty five", 0.75),

			(0.5, "decrease volume", 0.4),
			(0.5, "decrease the volume", 0.4),
			(0.5, "decrease volume by 40", 0.1),
			(0.5, "turn down the volume", 0.4),
			(0.5, "turn it down by 30", 0.2),
			(0.5, "turn it down by 20%", 0.3),
			(0.5, "volume down", 0.4),
			(0.5, "turn the volume down", 0.4),

			(0.5, "mute the sound", "mute"),
			(0.5, "unmute audio", "unmute"),
		]
		action_volume_set = volume_set.ActionVolumeSet()
		for current_vol, query, expected_result in test_set:
			with self.subTest(query=query):
				doc = nlp(query)
				sent = next(doc.sents)
				self.assertEqual(action_volume_set.parse(current_vol, sent), expected_result, msg=query)

	@given(query_format=st.one_of("turn up the volume by {}", "turn it up by {}", "increase volume by {}"), start_volume=st.floats(0, 1), increase=st.integers(1, 100), word_form=st.booleans())
	def prop_test_volume_increase(self, query_format, start_volume, increase, word_form):
		action_volume_set = volume_set.ActionVolumeSet()
		query = query_format.format(p.number_to_words(increase).replace("-", " ") if word_form else increase)
		doc = nlp(query)
		sent = next(doc.sents)
		self.assertEqual(action_volume_set.parse(start_volume, sent), start_volume + (increase / 100), msg=query)

	@given(query_format=st.one_of("turn down the volume by {}", "turn it down by {}", "decrease volume by {}"), start_volume=st.floats(0, 1), decrease=st.integers(1, 100), word_form=st.booleans())
	def prop_test_volume_decrease(self, query_format, start_volume, decrease, word_form):
		action_volume_set = volume_set.ActionVolumeSet()
		query = query_format.format(p.number_to_words(decrease).replace("-", " ") if word_form else decrease)
		doc = nlp(query)
		sent = next(doc.sents)
		self.assertEqual(action_volume_set.parse(start_volume, sent), start_volume - (decrease / 100), msg=query)

	@given(query_format=st.one_of("volume {}", "set volume to {}", "increase volume to {}", "decrease volume to {}", "turn it up to {}", "turn down the volume to {}", "put the volume at {}", "put volume at {}"), start_volume=st.floats(0, 1), target_volume=st.integers(0, 100), word_form=st.booleans())
	def prop_test_volume_set(self, query_format, start_volume, target_volume, word_form):
		action_volume_set = volume_set.ActionVolumeSet()
		query = query_format.format(p.number_to_words(target_volume).replace("-", " ") if word_form else target_volume)
		doc = nlp(query)
		sent = next(doc.sents)
		self.assertEqual(action_volume_set.parse(start_volume, sent), start_volume - (target_volume / 100), msg=query)

if __name__ == '__main__':
	unittest.main()
