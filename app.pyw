import json

from src.client import Client

try:
    with open('app.json') as f:
        __config = json.load(f)
except FileNotFoundError:
    __config = {}

client = Client(**__config)
client.run()
