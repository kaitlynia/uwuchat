import asyncio
import asyncio.exceptions as async_exc
import tkinter as tk
from traceback import print_exc

import configtool


class Client(tk.Tk):
    '''
    Simple uwuchat client implementation.
    '''

    MESSAGE_DELIMITER = b'\n'

    defaults = {
        "host": "localhost",
        "port": 8888,
        "user": "anon"
    }

    def __init__(self):
        # init Tcl + Toplevel widget
        super().__init__()

        # how fast Tcl can update
        self.gui_timeout = 0.001
        # TODO : show user that the config file does not exist
        self.config = configtool.read("client.json", Client.defaults)

        # asyncio items, assigned when Client.run() is executed
        self.loop: asyncio.AbstractEventLoop = None
        self.net_task: asyncio.Task = None
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None

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

    def pack_all(self):
        '''
        Display the application's widgets.
        '''
        self.messages.pack()
        self.entry.pack()
    
    async def send(self, data: bytes):
        '''
        Sends data to the server.
        '''
        print(f"[send] sending {data}...")
        self.writer.write(data)
        await self.writer.drain()
        print(f"[send] {data} sent")

    async def recv(self) -> bytes:
        '''
        Receives data from the server.
        '''
        print("[recv] waiting for data...")
        data = await self.reader.readuntil(Client.MESSAGE_DELIMITER)
        print(f"[recv] received {data}")
        return data

    def log(self, message: str, important=True):
        '''
        Appends messages to the messages `Listbox`.
        
        Messages default as `important`, scrolling down to the new message.
        '''
        self.messages.insert("end", message)
        if important:
            self.messages.see("end")

    def _entry_binding(self, event):
        '''
        Called when `<Return>` is pressed in the `Client.entry` Text widget.

        Schedules message data for transmission.
        '''
        if self.writer is None or self.writer.is_closing():
            return "break"

        # message has its leading and trailing whitespace stripped first
        if (message := self.entry.get("1.0", "end").strip()) != "":
            # then the user config attribute is joined with the message and encoded to bytes
            data = f"{self.config['user']}: {message}\n".encode()
            print(f"[_entry_binding] scheduling send task for data {data}...")
            self.loop.create_task(self.send(data))

        self.after_idle(self.entry.delete, "1.0", "end")
        return "break"

    async def net(self, host, port):
        '''
        Connect to a `host` and `port` and start network logic.

        This is called as a result of calling `Client.run` so you shouldn't need to call this manually.
        '''
        try:
            while True:
                self.log(f"[info] connecting to host {host} on port {port}...")
                self.reader, self.writer = await asyncio.open_connection(host, port)
                self.log("[info] connected")

                while not (self.reader.at_eof() or self.writer.is_closing()):
                    message = await self.recv()
                    # TODO : this is pretty naive, need to implement filters
                    self.log(message.decode()[:-1])

                self.log("[error] server connection closed")
                self.writer.close()

        except asyncio.CancelledError:
            self.log("[info] quitting...")
            if not self.writer.is_closing():
                self.writer.close()
            await self.writer.wait_closed()

        except:
            print_exc()

    def stop(self):
        '''
        Cancels the network task, which stops the event loop cleanly.
        '''
        self.net_task.cancel()

    async def _async_run(self):
        '''
        Sets up asyncio-related stuff and starts updating Tcl.
        '''

        # state + tkinter config
        self.protocol("WM_DELETE_WINDOW", self.stop)
        self.wm_title("uwuchat")

        # asyncio stuff
        self.loop = asyncio.get_running_loop()
        self.outbox = asyncio.Queue()

        # use client config to create the network task
        self.net_task = asyncio.create_task(self.net(self.config["host"], self.config["port"]))

        # draw the GUI at least once so that info/errors can be posted to the messages Listbox
        self.pack_all()
        self.update()

        # update GUI until the net task is cancelled, use async wrapper to execute scheduled asyncio tasks first
        while not self.net_task.done():
            await asyncio.sleep(self.gui_timeout, self.update())

        # wait for the net task to finish after it is cancelled so that the writer object is closed properly
        await self.net_task

    def run(self):
        '''
        Runs the client application.
        '''
        asyncio.run(self._async_run())

if __name__ == "__main__":
    client = Client()
    client.run()
