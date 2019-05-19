#!.env/bin/python3
import argparse
import crystal.core
import logging, coloredlogs

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="voice", const='voice', nargs='?', choices=["voice", "text"], required=False)
parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Set logger log level (default: INFO).")
parser.add_argument("--verbose", action='store_true', help="Increase verbosity (within confines of provided log level).")
parser.add_argument("--disable-actions", nargs="+", required=False, help="Disable the specified actions (default: )")

args = parser.parse_args()

# TODO: refactor how queries work, like you did with reponses
# Currently, we just pass a spacy doc to the action.
# Instead, we'll start passing some kind of query object.
# Each query will have an ID.
# When a query is made, the audio is saved to file in the cache.
# Query objects will have 2 properties, the query as a string, and the query as a spacy doc.

# TODO: allow actions to provide context strings for speech recognition result filtering

if __name__ == "__main__":
	# set up log levels
	coloredlogs.install(level=args.log_level)
	if args.verbose:
		logging.getLogger("blink1.blink1").setLevel(logging.DEBUG)
	else:
		logging.getLogger("blink1.blink1").setLevel(logging.INFO)

	crystal.core.run(args)