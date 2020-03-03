import asyncio
import asyncio.exceptions as async_exc
import tkinter as tk
from traceback import print_exc

import configtool


class Client(tk.Tk):
    '''
    Simple uwuchat client implementation.
    '''

    defaults = {
        "server": "localhost",
        "port": 8888,
        "user": "anon"
    }

    def __init__(self):
        # init Tcl + Toplevel widget
        super().__init__()

        # running state + how fast Tcl can update + config
        self.running = False
        self.tcl_timeout = 0.001
        # TODO : show user that the config file does not exist
        self.config = configtool.read("client", self.defaults)

        # asyncio items, assigned when Client.run() is executed
        self.loop: asyncio.AbstractEventLoop = None
        self.net_task: asyncio.Task = None
        self.writers = []
        self.outbox: asyncio.Queue = None

        # width of the whole client (in characters)
        self.width = 40

        # tkinter widgets
        self.messages = tk.Listbox(
            master = self,
            width = self.width + 13,
            height = 12
        )
        self.entry = tk.Text(
            master = self,
            width = self.width,
            height = 3
        )
        self.entry.bind("<Return>", self._entry_binding)

    def show(self):
        '''
        Show the client's widgets.
        '''
        self.messages.pack()
        self.entry.pack()

    def _entry_binding(self, event):
        '''
        Called when `<Return>` is pressed in the `Client.entry` Text widget.
        '''
        message = self.entry.get("1.0", "end").strip()
        if message != "":
            self.outbox.put_nowait(f"{self.config['user']}: {message}\n")
        self.after_idle(self.entry.delete, "1.0", "end")

    async def net(self, host, port):
        '''
        Connect to a `host` and `port` and start network logic.

        This is called in `Client.run()` so you shouldn't need to call this manually.
        '''
        while self.running:
            try:
                reader, writer = await asyncio.open_connection(host, port)
                self.writers.append(writer)
                await asyncio.gather(
                    self._recv_loop(reader),
                    self._send_loop(writer)
                )
            except:
                print_exc()

    async def _recv_loop(self, reader: asyncio.StreamReader):
        '''
        Receives messages from `reader` and puts them in `Client.inbox`
        '''
        while self.running:
            try:
                message = await reader.readuntil()
                self.loop.create_task(self.process_message(message))
            except:
                print_exc()

    async def _send_loop(self, writer: asyncio.StreamWriter):
        '''
        Gets messages from `Client.outbox` and sends messages to `writer`
        '''
        while self.running:
            try:
                message = await self.outbox.get()
                writer.write(message.encode())
                self.loop.create_task(writer.drain())
            except:
                print_exc()

    async def process_message(self, message: bytes):
        '''
        Processes messages.
        '''
        try:
            # This method is only async so that additional network I/O could be started here as needed
            # TODO : this is pretty naive, need to implement filters
            self.messages.insert("end", message.decode())
            self.messages.see("end")
        except:
            print_exc()

    def stop(self):
        '''
        Signal for Client.start() to finish, sanely stopping the event loop.
        '''
        self.running = False

    async def _async_run(self):
        '''
        Start the client. Sets up asyncio-related stuff and starts updating Tcl.
        '''

        # state + tkinter config
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.stop)
        self.wm_title("uwuchat")
        self.show()

        # asyncio stuff
        self.loop = asyncio.get_running_loop()
        self.outbox = asyncio.Queue()

        # use client config to create the network task
        server = self.config["server"].split(":")
        host, port = server[0], int(server[1]) if 1 in server else self.config["port"]
        self.net_task = asyncio.create_task(self.net(host, port))

        # update Tcl until client is closed
        # sleep is ordered first so that the UI is only drawn after a connection is established
        while self.running:
            await asyncio.sleep(self.tcl_timeout)
            self.update()

        # cleanup before exit
        for writer in self.writers:
            writer.close()

        await asyncio.gather(*(writer.wait_closed() for writer in self.writers))

    def run(self):
        asyncio.run(self._async_run())


client = Client()
client.run()
