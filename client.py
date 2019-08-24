from tkinter import *
import asyncio
import os


# Constants
START = "1.0"
DELIMITER = "\n"
ANY_KEY = "<Key>"
RETURN_KEY = "<Return>"
SHIFT_RETURN = "<Shift-Return>"
# this is pretty gross, maybe come up with a better way to express this
INSERTABLE = set("`1234567890-=qwertyuiop[]\\\
asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}\
|ASDFGHJKL:\"ZXCVBNM<>? ")
ENCODING = "utf8"
MESSAGE_SOUND = "sounds/message.wav"
MENTION_SOUND = "sounds/mention.wav"


# Determine if notification sounds can be played
# TODO cross-platform
on_windows = os.name == 'nt'
if on_windows:
    import winsound

# Set current working directory here
os.chdir(os.path.dirname(os.path.realpath(__file__)))


class App(Tk):
    """
    An `App` has an associated `ServerManager` and is the top-level object of the client.

    You can supply any keyword arguments that `Tk` accepts.
    """

    default_color = "white"
    default_font = "Consolas 14"

    app_config = {
        "bg": "#111",
        "padx": 10,
        "pady": 8
    }

    label_config = {
        "bg": app_config["bg"],
        "fg": default_color,
        "font": default_font,
    }

    text_entry_config = {
        "bg": "#222",
        "fg": default_color,
        "insertbackground": "#FFF",
        "font": default_font,
        "padx": app_config["padx"],
        "pady": app_config["pady"],
        "wrap": WORD,
    }

    text_config = {
        "bg": app_config["bg"],
        "fg": default_color,
        "insertbackground": app_config["bg"],
        "font": default_font,
        "padx": app_config["padx"],
        "pady": app_config["pady"],
        "wrap": WORD,
        "spacing3": 4,
        "state": DISABLED,
    }

    def __init__(self, sm_name="anon", sm_server="tk.hazel.cafe", sm_notify=True, **kwargs):
        super().__init__(**kwargs)

        self.config(**self.app_config)
        self.server_manager = ServerManager(self, sm_name, sm_server, sm_notify)


class ServerManager:
    """
    A `ServerManager` allows users to connect to servers from a task and some widgets.
    """

    def __init__(self, app, name, host, notify):
        self.app = app
        self.default_notify = notify
        self.servers = {}

        self.name_label = Label(**app.label_config, text="Name")
        self.name_entry = Text(**app.text_entry_config, width=30, height=1)
        self.name_entry.insert(START, name)
        self.name_entry.bind(RETURN_KEY, self._enter_server)

        self.server_label = Label(**app.label_config, text="Server")
        self.server_entry = Text(**app.text_entry_config, width=30, height=1)
        self.server_entry.insert(START, host)
        self.server_entry.bind(RETURN_KEY, self._enter_server)

        self._connect_queue = asyncio.Queue()
        self._connect_task = asyncio.create_task(self._connect_loop())

    def _enter_server(self, event):
        """
        Called when `<Return>` is pressed.
        """
        name = self.name_entry.get(START, END).strip()
        host = self.server_entry.get(START, END).strip()
        if name != "" and host != "":
            self._connect_queue.put_nowait((name, host))

    async def _connect_loop(self):
        """
        Starts when `ServerManager._connect_task` is run.
        """
        while True:
            name, host = await self._connect_queue.get()
            if host not in self.servers:
                server = Server(self.app, name, host, notify=self.default_notify)
                if await server.connect():
                    self.servers[host] = server

    def show(self, focus=True):
        """
        Shows the name label + entry and the server label + entry.

        If `focus` is `True`, the name entry takes focus.
        """
        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1)
        if focus:
            self.name_entry.focus_set()

        self.server_label.grid(row=1, column=0)
        self.server_entry.grid(row=1, column=1)

    def hide(self):
        """
        Hides the name label + entry and the server label + entry.
        """
        self.name_label.grid_forget()
        self.name_entry.grid_forget()
        self.server_label.grid_forget()
        self.server_entry.grid_forget()


class Server:
    """
    A `Server` contains all the logic necessary to send and receive data from a server.
    They also hold the related GUI widgets and their bindings.
    """

    def __init__(self, app, name, host, port=8888, notify=True):
        self.app = app
        self.name = name
        self.host = host
        self.port = port
        self.notify = notify

        self.chat_log = Text(**app.text_config)
        self.message_entry = Text(**app.text_entry_config, height=3)

        self.chat_log.bind(ANY_KEY, self._enter_key)
        self.chat_log.bind(RETURN_KEY, self._enter_message)
        self.message_entry.bind(SHIFT_RETURN, self._enter_key)
        self.message_entry.bind(RETURN_KEY, self._enter_message)

        self._reader = None
        self._writer = None
        self._send_queue = asyncio.Queue()
        self._send_task = None
        self._recv_task = None
        self._recv_prefix = ""
        self._mention = f"@{self.name}"

    def _enter_key(self, event):
        """
        Called when a `<Key>` is pressed.
        """
        if event.char in INSERTABLE:
            self.message_entry.focus_set()
            self.message_entry.insert(INSERT, event.char)

    def _enter_message(self, event):
        """
        Called when `<Return>` is pressed.
        """
        message = self.message_entry.get(START, END).strip()
        if message:
            self._send_queue.put_nowait(f"{self.name}: {message}\n")
        self.app.after_idle(self.message_entry.delete, START, END)

    def _handle_message(self, message):
        """
        Takes a message and (in the future) produces a JSON object (or stanza).

        Inserts the relevant information in the chat log.
        Notifies the client if applicable.

        JSON data model is not implemented yet, so it inserts the entire message.
        """
        # TODO actually parse messages
        stanza = f"{self._recv_prefix}{message.strip().decode(ENCODING)}"
        self.chat_log.config(state=NORMAL)
        self.chat_log.insert(END, stanza)
        self.chat_log.config(state=DISABLED)
        self.chat_log.see(END)

        if self.notify and on_windows:
            self._do_notification(stanza)

    def _do_notification(self, stanza):
        """
        Plays a notification sound if the app is not focused.

        Currently Windows-only.
        """
        if self.app.focus_get() is None:
            sound = MENTION_SOUND if self._mention in stanza else MESSAGE_SOUND
            winsound.PlaySound(sound,
            winsound.SND_FILENAME |
            winsound.SND_ASYNC |
            winsound.SND_NOSTOP)

    async def _send_loop(self):
        """
        Starts when `Server._send_task` is run.
        """
        try:
            while True:
                self._writer.write((await self._send_queue.get()).encode(ENCODING))
                await self._writer.drain()
        except Exception as e:
            print(f"{repr(e)} in Server._send_loop")

    async def _recv_loop(self):
        """
        Starts when `Server._recv_task` is run.
        """
        try:
            message = await self._reader.readuntil()
            self._handle_message(message)
            self._recv_prefix = "\n"
            while True:
                message = await self._reader.readuntil()
                self._handle_message(message)
        except Exception as e:
            print(f"{repr(e)} in Server._recv_loop")

    def show(self, focus=True):
        """
        Shows the chat log and message entry.

        If `focus` is `True`, the message entry takes focus.
        """
        self.chat_log.pack()
        self.message_entry.pack()
        if focus:
            self.message_entry.focus_set()

    def hide(self):
        """
        Hides the chat log and message entry.
        """
        self.chat_log.pack_forget()
        self.message_entry.pack_forget()

    async def connect(self):
        """
        Connects to the server.

        Currently, it does not attempt to resume operating after an exception occurs.
        """
        if all(not t or t.done() for t in (self._send_task, self._recv_task)) and\
            not self._writer or self._writer.is_closing():
            try:
                self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
                self._send_task = asyncio.create_task(self._send_loop())
                self._recv_task = asyncio.create_task(self._recv_loop())
                # TODO make a toggle menu for the server manager instead of showing + hiding it
                self.app.server_manager.hide()
                self.show()
                return True
            except Exception as e:
                print(f"{repr(e)} in Server.connect")
        return False


async def launch_app(update_timeout=0.01):
    """
    Sets up the GUI and sleeps every `update_timeout` seconds to allow other tasks to run.
    """
    app = App()

    app.protocol("WM_DELETE_WINDOW", asyncio.get_event_loop().stop)
    app.wm_title("TkChat")

    app.server_manager.show()

    while True:
        app.update()
        await asyncio.sleep(update_timeout)


if __name__ == "__main__":
    try:
        # 🚀
        asyncio.run(launch_app())
    except RuntimeError as e:
        # Ignore a specific exception raised during a normal exit
        if e.args[0] != "Event loop stopped before Future completed.":
            raise
