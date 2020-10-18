from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import feedback
import utils
import logging
from pathlib import Path
import csv
log = logging.getLogger(__name__)

class ActionStoLore(BaseAction):
	"""docstring for ActionStoLore."""
	def __init__(self):
		super(ActionStoLore, self).__init__()
		self.handled_classifier = "sto-lore"
		self.requires_updater = False

	@classmethod
	def get_lore_answer(self, volume, chapter):
		lore_path = Path(__file__).parent / "lore.csv"
		with lore_path.open("r") as f:
			csv_reader = csv.reader(f, delimiter=',')
			line_count = 0
			for row in csv_reader:
				if line_count == 0:
					line_count += 1
					continue
				if int(row[0]) == volume and int(row[1]) == chapter:
					return row[3]
				line_count += 1

	@classmethod
	def parse(self, doc):
		volume_token = utils.find_word(doc, "volume")
		chapter_token = utils.find_word(doc, "chapter")
		nums = [utils.select_number_bleedy(volume_token.nbor(1)).text, utils.select_number_bleedy(chapter_token.nbor(1)).text]
		def _to_num(text):
			if text == "to":
				return 2
			elif text == "for":
				return 4
			try:
				return int(text)
			except ValueError:
				return utils.text2int(text)
		return map(_to_num, nums)

	@classmethod
	def run(self, doc):
		volume, chapter = self.parse(doc)
		log.info(f"volume: {volume}, chapter: {chapter}")

		if volume and chapter and volume >= 1 and chapter >= 1:
			answer = self.get_lore_answer(volume, chapter)
			log.info(f"lore answer: {answer}")
			return ActionResponseQuery(answer)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, f"volume needs to be >= 1, got {volume} and chapter needs to be >= 1, got {chapter}")

def getAction():
	return ActionStoLore()
