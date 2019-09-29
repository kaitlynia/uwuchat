import json


def read(name: str, defaults: dict):
    try:
        with open(f"{name}.json") as f:
            return json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return defaults.copy()
