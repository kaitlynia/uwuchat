import asyncio
import asyncio.exceptions as async_exc
import tkinter as tk

import configtool


class Client(tk.Tk):
    '''
    Simple uwuchat client implementation.
    '''

    DEFAULT_PORT = 8888

    def __init__(self):
        # init Tcl + Toplevel widget
        super().__init__()

        # running state + how fast Tcl can update + config
        self.running = False
        self.tcl_timeout = 0.001
        # TODO : show user that the config file does not exist
        self.config, self.configured = configtool.read("client",
            default_user = "anon",
            default_server = "localhost"
        )
        self.user = self.config.get("client", "default_user")

        # asyncio items, assigned when Client.run() is executed
        self.loop: asyncio.AbstractEventLoop = None
        self.net_task: asyncio.Task = None
        self.inbox_task: asyncio.Task = None
        self.inbox: asyncio.Queue = None
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
            self.outbox.put_nowait(f"{self.user}: {message}\n")
        self.after_idle(self.entry.delete, "1.0", "end")

    async def net(self, host, port):
        '''
        Connect to a `host` and `port` and start network logic.

        This is called in `Client.run()` so you shouldn't need to call this manually.
        '''
        while self.running:
            try:
                async with asyncio.connect(host, port) as stream:
                    await asyncio.gather(
                        self._send_loop(stream),
                        self._recv_loop(stream)
                    )
            except Exception as e:
                print(f"\nException in Client.net:\n{e}")

    async def _send_loop(self, stream):
        '''
        Gets messages from `Client.outbox` and sends messages to `stream`
        '''
        while self.running:
            try:
                message = await self.outbox.get()
                await stream.write(message.encode())
            except Exception as e:
                print(f"\nException in Client.send_loop:\n{e}")

    async def _recv_loop(self, stream):
        '''
        Receives messages from `stream` and puts them in `Client.inbox`
        '''
        while self.running:
            try:
                message = await stream.readuntil()
                self.inbox.put_nowait(message)
            except Exception as e:
                print(f"\nException in Client.recv_loop:\n{e}")

    async def _inbox_loop(self):
        '''
        Monitors the inbox and processes messages.
        '''
        while self.running:
            try:
                message = await self.inbox.get()
                # TODO : this is pretty naive, need to implement filters
                self.messages.insert("end", message.decode())
                self.messages.see("end")
            except Exception as e:
                print(f"\nException in Client.inbox_loop:\n{e}")

    def stop(self):
        '''
        Signal for Client.start() to finish, sanely stopping the event loop.
        '''
        self.running = False

    async def start(self):
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
        self.inbox = asyncio.Queue()
        self.outbox = asyncio.Queue()

        # use client config to create the network task
        server = self.config.get("client", "default_server").split(":")
        host, port = server[0], int(server[1]) if 1 in server else self.DEFAULT_PORT
        self.net_task = asyncio.create_task(self.net(host, port))

        # just before updating Tcl, create the inbox task that handles incoming messages
        self.inbox_task = asyncio.create_task(self._inbox_loop())

        # update Tcl until client is closed
        while self.running:
            self.update()
            await asyncio.sleep(self.tcl_timeout)

client = Client()
asyncio.run(client.start())
