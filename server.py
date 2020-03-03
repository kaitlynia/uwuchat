import asyncio
import asyncio.exceptions as async_exc
from traceback import print_exc

import configtool

# import sqlite3

# db = sqlite3.connect("server.db")

class Server:

    MESSAGE_DELIMITER = b'\n'

    defaults = {
        "port": 8888
    }

    def __init__(self):
        self.loop: asyncio.AbstractEventLoop = None # assigned in _async_run
        self.server: asyncio.AbstractServer = None  # assigned in _async_run

        self.config = configtool.read("server.json", Server.defaults)
        self.readers = []
        self.writers = []

    async def broadcast(self, message):
        for writer in self.writers:
            writer.write(message)

        await asyncio.gather(*(writer.drain() for writer in self.writers))

    async def on_connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.readers.append(reader)
        self.writers.append(writer)
        try:
            while not writer.is_closing():
                message = await reader.readuntil(Server.MESSAGE_DELIMITER)
                self.loop.create_task(self.broadcast(message))
        # except (ConnectionResetError, async_exc.IncompleteReadError) as e:
        except:
            print_exc()
        self.readers.remove(reader)
        self.writers.remove(writer)

    async def _async_run(self):
        self.loop = asyncio.get_running_loop()
        self.server = await asyncio.start_server(self.on_connect, port=self.config["port"])
        await self.server.serve_forever()

    def run(self):
        asyncio.run(self._async_run())

server = Server()

try:
    server.run()
except KeyboardInterrupt:
    pass
