# tkchat
A chat application written in Python with tkinter

### Goals
- Have no dependencies (besides Python and its standard library of course)
- Utilize single threaded concurrency for the client and the server
- Offer stateful client API with GUI "baked in"
- Design JSON "stanzas" as a formal specification
- Implement E2E or OMEMO encryption

### Non-goals
- Be strictly efficient
- Federate with other servers (this may change in the future)

### Installation

[Python 3.8](https://www.python.org/downloads/) is required to run both the client and the server application.

Once it is installed, you can run the client by entering `py client.py` in Command Prompt on Windows
or `python3 client.py` in a Linux terminal.

The server can be run the same way. You can also specify a `client.json` file where `client.py` resides and you can
customize some of the options the client uses. An example is provided in `example-client.json`
