import asyncio
import asyncio.exceptions as async_exc

import configtool

# import sqlite3

# db = sqlite3.connect("server.db")

class Server:
    def __init__(self):
        self.config, self.configured = configtool.read("server",
            port = "8888"
        )
        self.port = self.config.get("server", "port")
        self.streams = []

    async def broadcast(self, message):
        await asyncio.gather(*(stream.write(message) for stream in self.streams))

    async def on_connect(self, stream):
        self.streams.append(stream)
        try:
            while not stream.is_closing():
                await self.broadcast(await stream.readuntil())
        except (ConnectionResetError, async_exc.IncompleteReadError) as e:
            print(stream, "RESULTED IN", e)
        self.streams.remove(stream)

    async def run(self):
        async with asyncio.StreamServer(self.on_connect, port=self.port) as ss:
            await ss.serve_forever()

server = Server()

try:
    asyncio.run(server.run())
except KeyboardInterrupt:
    pass
