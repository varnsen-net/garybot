""""""
import ssl

import gevent
from gevent.queue import Queue, Empty
from loguru import logger


class Writer(gevent.Greenlet):
    """A greenlet that sends lines to the IRC server. Lines are put into the
    inbox queue, and the greenlet takes care of encoding and sending them.

    Attributes:
        inbox (Queue): A queue of lines to send to the server. Lines should be
            strings without newlines; the greenlet will append \r\n and encode
            them before sending.
        _socket (socket): The socket object used to send data to the server.
            Should be a connected socket.
        _encoding (str): The character encoding to use when encoding lines
            before sending. Defaults to 'utf-8'.
        _stop_event (Event): A gevent event that signals the greenlet to stop.
    """

    def __init__(self, socket, stop_event, encoding='utf-8'):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._socket = socket
        self._encoding = encoding
        self._stop_event = stop_event

    def _send(self, line):
        """Encode and send a single IRC line (newline appended automatically).

        :param str line: The line to send to the server. Should not include
            newlines; the method will append \r\n before encoding and sending.
        :return: None
        :rtype: None
        """
        if not self._socket:
            raise OSError("Not connected")
        raw = (line + "\r\n").encode(self._encoding)
        try:
            self._socket.sendall(raw)
        except (OSError, ssl.SSLError) as exc:
            logger.error(f"Send failed: {exc}")
            raise

    def _run(self):
        """The main loop of the greenlet. Continuously checks the inbox for
        lines to send, and sends them until the stop event is set.

        :return: None
        :rtype: None
        """
        logger.info("Writer started.")
        while not self._stop_event.is_set():
            try:
                line = self.inbox.get(timeout=1)
            except Empty:
                continue
            self._send(line)
