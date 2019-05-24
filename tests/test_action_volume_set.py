import unittest
import spacy
from crystal.actions import volume_set

nlp = None

class TestActionVolumeSet(unittest.TestCase):
	"""docstring for TestActionVolumeSet."""

	@classmethod
	def setUpClass(self):
		global nlp
		nlp = spacy.load("en")

	def test_action_volume_set(self):
		# current_volume, query string, expected result
		test_set = [
			(0.5, "set volume to 80%", 0.8),
			(0.5, "set volume to 20 percent", 0.2),
			(0.5, "set volume to 40", 0.4),
			(0.5, "turn it up to 70", 0.7),
			(0.5, "turn it down to 20", 0.2),

			(0.5, "increase volume", 0.6),
			(0.5, "increase the volume", 0.6),
			(0.5, "increase volume by 40", 0.9),
			(0.5, "turn up the volume", 0.6),
			(0.5, "turn it up by 30", 0.8),
			(0.5, "Turn It Up by 20%", 0.7),

			(0.5, "decrease volume", 0.4),
			(0.5, "decrease the volume", 0.4),
			(0.5, "decrease volume by 40", 0.1),
			(0.5, "turn down the volume", 0.4),
			(0.5, "turn it down by 30", 0.2),
			(0.5, "turn it down by 20%", 0.3),

			(0.5, "mute the sound", "mute"),
			(0.5, "unmute audio", "unmute"),
		]
		action_volume_set = volume_set.ActionVolumeSet()
		for current_vol, query, expected_result in test_set:
			doc = nlp(query)
			sent = next(doc.sents)
			self.assertEqual(action_volume_set.parse(current_vol, sent), expected_result, msg=query)

if __name__ == '__main__':
	unittest.main()
