import os
import requests
from pathlib import Path

from crystal.actions import BaseAction
from crystal.actions.responses import *
from crystal import core, feedback
import utils
import logging
log = logging.getLogger(__name__)

API_URL_CURRENT_WEATHER = "https://api.openweathermap.org/data/2.5/weather?appid={}&zip={},us&units=imperial"

class ActionWeather(BaseAction):
	"""docstring for ActionWeather."""
	def __init__(self):
		super(ActionWeather, self).__init__()
		self.handled_classifier = "weather"
		self.requires_updater = False

	@classmethod
	def parse(self, doc):
		word = utils.find_word(doc, "tomorrow")
		if word:
			return "forecast"
		return "current"

	@classmethod
	def get_city_name(self, zipcode):
		zipcode_cache = {}
		zipcode_cache_path = Path("/home/carson/.cache/crystal/weather/zipcodes.cache")

		if zipcode_cache_path.exists():
			with zipcode_cache_path.open("r") as zipcode_cache_file:
				for line in zipcode_cache_file:
					if "=" not in line:
						continue
					spl = line.split("=")
					zipcode_cache[spl[0]] = spl[1]

			if zipcode in zipcode_cache.keys():
				log.debug("Found zipcode {} in cache: {}".format(zipcode, zipcode_cache[zipcode]))
				return zipcode_cache[zipcode].strip()
		else:
			log.debug("No zipcode cache, creating new: {}".format(str(zipcode_cache_path.parent)))
			zipcode_cache_path.parent.mkdir(parents=True, exist_ok=True)

		zipcode_api_key = core.get_config("zipcode_api_key")
		if not zipcode_api_key:
			log.error("Failed to get `zipcode_api_key` from config")
			return None

		resp = requests.get("https://www.zipcodeapi.com/rest/{}/info.json/{}/degrees".format(zipcode_api_key, zipcode))
		data = resp.json()
		city_result = "{}, {}".format(data["city"], data["state"])
		zipcode_cache[zipcode] = city_result

		with zipcode_cache_path.open("w") as zipcode_cache_file:
			for code in zipcode_cache:
				print("{}={}".format(code, zipcode_cache[code]), file=zipcode_cache_file)
		return city_result

	@classmethod
	def run(self, doc):
		command = self.parse(doc)

		if command == "current":
			zipcode = core.get_config("zipcode")
			if not zipcode:
				return ActionResponseBasic(ActionResponseType.FAILURE, "Failed to get `zipcode` from config")

			openweather_api_key = core.get_config("openweathermap_api_key")
			if not openweather_api_key:
				return ActionResponseBasic(ActionResponseType.FAILURE, "Failed to get `openweathermap_api_key` from config")

			resp = requests.get(API_URL_CURRENT_WEATHER.format(openweather_api_key, zipcode))
			if resp.status_code != 200:
				return ActionResponseBasic(ActionResponseType.FAILURE, "weather API query failed: {}, {}".format(resp.status_code, resp.json()))
			log.debug("Weather API success: 200")
			current_weather = resp.json()
			log.debug(current_weather)

			# SAMPLE RESPONSE: https://samples.openweathermap.org/data/2.5/weather?zip=94040,us&appid=b6907d289e10d714a6e88b30761fae22
			city_name = self.get_city_name(zipcode)
			status_curr = current_weather["weather"][0]["main"]
			temp_curr = current_weather["main"]["temp"]
			temp_low = current_weather["main"]["temp_min"]
			temp_high = current_weather["main"]["temp_max"]
			result_string = "Current Weather in {}: \n{}, {} ({}/{})".format(city_name, status_curr, temp_curr, temp_low, temp_high)
			return ActionResponseQuery(result_string)
		else:
			return ActionResponseBasic(ActionResponseType.FAILURE, "unknown command: {}".format(command))

def getAction():
	return ActionWeather()
