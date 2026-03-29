""""""
import socket

import gevent
from loguru import logger


class Listener(gevent.Greenlet):
    """Listens for incoming lines on a socket and puts them in the dispatcher's
    inbox.

    Attributes:
        _BUFFER_SIZE (int): The number of bytes to read from the socket at a time.
        _dispatcher (Dispatcher): The dispatcher to which received lines are sent.
        _socket (socket.socket): The socket from which to read incoming data.
        _encoding (str): The encoding used to decode incoming bytes into strings.
        _recv_buffer (str): A buffer to hold incomplete lines until they are complete.
        _stop_event (gevent.event.Event): An event that signals the listener to stop.
    """

    _BUFFER_SIZE = 4096

    def __init__(self, dispatcher, socket, stop_event, encoding='utf-8'):
        gevent.Greenlet.__init__(self)
        self._dispatcher = dispatcher
        self._socket = socket
        self._encoding = encoding
        self._recv_buffer = ""
        self._stop_event = stop_event

    def _recv_lines(self):
        """Read from the socket into a line buffer and return complete lines.

        Raises OSError on disconnect so the caller can trigger reconnection.
        """
        try:
            chunk = self._socket.recv(self._BUFFER_SIZE)
        except socket.timeout:
            return []    # nothing arrived — keep looping
        if not chunk:
            raise OSError("Server closed the connection")
        try:
            text = chunk.decode(self._encoding)
        except UnicodeDecodeError:
            text = chunk.decode("latin-1")
        self._recv_buffer += text
        *complete, self._recv_buffer = self._recv_buffer.split("\r\n")
        return complete

    def _run(self):
        """Process incoming lines until an error or clean shutdown."""
        logger.info("Listener started.")
        while not self._stop_event.is_set():
            try:
                for line in self._recv_lines():
                    line = line.strip()
                    if line:
                        self._dispatcher.inbox.put(line)
            except OSError as e:
                if not self._stop_event.is_set():
                    logger.error(f"Listener error: {e}")
                    self._stop_event.set()  # trigger shutdown
                    raise # re-raise so greenlet is marked as failed


