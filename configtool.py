import json


def read(filename: str, defaults: dict):
    try:
        with open(filename) as f:
            return json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return defaults.copy()
