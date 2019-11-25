import asyncio

import uwuspec

# hex(PORT) == '0xcafe'!
port = 51966
last_id = 0
all_streams = {}
streamerator = all_streams.values()


async def on_message(stream: uwuspec.Stream, stanza: uwuspec.Stanza):
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    for each_stream in streamerator:
        loop.create_task(each_stream.write_stanza(stanza))

async def on_error(stream: uwuspec.Stream, stanza: uwuspec.Stanza):
    pass

async def on_hello(stream: uwuspec.Stream, stanza: uwuspec.Stanza):
    pass

async def on_bye(stream: uwuspec.Stream, stanza: uwuspec.Stanza):
    pass

async def on_unknown(stream: uwuspec.Stream, stanza: uwuspec.Stanza):
    pass

events = {
    uwuspec.Variant.Message: on_message,
    uwuspec.Variant.Error: on_error,
    uwuspec.Variant.Hello: on_hello,
    uwuspec.Variant.Bye: on_bye,
    uwuspec.Variant.Unknown: on_unknown
}


async def on_connect(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter):

    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    stream = uwuspec.Stream(reader, writer)

    # ignore this Stream if it doesn't say Hello first
    stanza = await stream.read_stanza()
    if stanza is None or stanza.variant is not uwuspec.Variant.Hello:
        return
    print(f"Hello, {writer.get_extra_info('socket')}")

    # throw this boy in the streamerator
    global last_id
    last_id += 1
    all_streams[last_id] = stream
    stream_id = last_id

    try:
        while not reader.at_eof():
            try:
                stanza = await stream.read()
                if stanza.variant is uwuspec.Variant.Bye:
                    break
                loop.create_task(events[stanza.variant](stream, stanza))
            except uwuspec.StanzaDecodeError:
                continue
    except (ConnectionResetError, asyncio.exceptions.IncompleteReadError) as e:
        print(e)

    # cya
    del all_streams[stream_id]


async def main():
    # create server
    server: asyncio.AbstractServer = await asyncio.start_server(on_connect, port=port)
    async with server:
        try:
            # start serving
            await server.serve_forever()
        except (KeyboardInterrupt, asyncio.CancelledError):
            # if CancelledError is propagated or the program is interrupted, leave context manager
            pass


asyncio.run(main())
