import asyncio

PORT = 8888
streams = set()

async def broadcast(message):
    for stream in streams:
        await stream.write(message)

async def on_connect(stream):
    streams.add(stream)
    try:
        while not stream.is_closing():
            await broadcast(await stream.readuntil())
    except (ConnectionResetError, asyncio.exceptions.IncompleteReadError) as e:
        pass
    streams.remove(stream)

async def main():
    async with asyncio.StreamServer(on_connect, port=PORT) as server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass