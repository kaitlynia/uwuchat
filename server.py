import asyncio
import asyncio.exceptions as async_exc

import configtool

# import sqlite3

# TODO : show user that the config file does not exist
config, ok = configtool.read("server", {
    "port": "8888"
})

# db = sqlite3.connect("server.db")

streams = []

async def broadcast(message):
    await asyncio.gather(*(stream.write(message) for stream in streams))

async def on_connect(stream):
    streams.append(stream)
    try:
        while not stream.is_closing():
            await broadcast(await stream.readuntil())
    except (ConnectionResetError, async_exc.IncompleteReadError) as e:
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
