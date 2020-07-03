from pathlib import Path
import pickle

persistence_base_path = Path.home() / ".crystal/"
if not persistence_base_path.exists():
	persistence_base_path.mkdir()

def get_state_for_module(module: str):
	if not persistence_base_path.exists():
		persistence_base_path.mkdir()

	state_file = persistence_base_path / f"state-{module}.pkl"
	if not state_file.exists():
		return None
	with state_file.open("rb") as f:
		return pickle.load(f)

def save_state_for_module(module: str, obj):
	if not persistence_base_path.exists():
		persistence_base_path.mkdir()

	state_file = persistence_base_path / f"state-{module}.pkl"
	if not state_file.exists():
		state_file.touch()
	with state_file.open("wb") as f:
		return pickle.dump(obj, f)
