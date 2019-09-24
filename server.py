import asyncio
import configparser
import sqlite3
from asyncio.exceptions import *

config = configparser.ConfigParser()
config.read("server.conf")

db = sqlite3.connect("server.db")

streams = []

async def broadcast(message):
    await asyncio.gather(*(stream.write(message) for stream in streams))

async def on_connect(stream):
    streams.append(stream)
    try:
        while not stream.is_closing():
            await broadcast(await stream.readuntil())
    except (ConnectionResetError, IncompleteReadError) as e:
        print(stream, "RESULTED IN", e)
    streams.remove(stream)

async def main():
    port = config.get("server", "port")
    async with asyncio.StreamServer(on_connect, port=port) as server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
