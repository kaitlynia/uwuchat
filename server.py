import asyncio

PORT = 8888
streams = set()

async def broadcast(message):
    for stream in streams:
        stream[1].write(message)
        await stream[1].drain()

async def on_connect(reader, writer):
    streams.add((reader, writer))
    print("Client connected")
    try:
        while not reader.at_eof():
            await broadcast(await reader.readline())
    except (ConnectionResetError, asyncio.exceptions.IncompleteReadError) as e:
        pass
    print("Client disconnected")
    streams.remove((reader, writer))

async def main():
    print("serving on port", PORT)
    server = await asyncio.start_server(on_connect, port=PORT)
    await server.serve_forever()

try:
    asyncio.get_event_loop().run_until_complete(main())
except KeyboardInterrupt:
    pass