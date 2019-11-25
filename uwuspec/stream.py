import asyncio
from .stanza import Stanza, StanzaDecodeError


class Stream:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read(self) -> bytes:
        return await self.reader.readuntil(Stanza.END)

    async def write(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()

    async def read_stanza(self) -> Stanza:
        try:
            return Stanza(await self.read())
        except StanzaDecodeError:
            return None

    async def write_stanza(self, stanza: Stanza):
        self.write(stanza.data)