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
        self.inbox = Queue(maxsize=100)
        self._socket = socket
        self._encoding = encoding
        self._stop_event = stop_event

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
            try:
                self._send(line)
            except (OSError, ssl.SSLError) as exc:
                logger.error(f"Error sending line: {exc}")
                self._stop_event.set()
                raise
            except ValueError as exc:
                logger.error(f"Invalid line: {exc}")
                continue
        logger.info("Writer stopped.")

    def _send(self, line):
        """Encode and send a single IRC line (newline appended automatically).

        :param str line: The line to send to the server. Should not include
            newlines; the method will append \r\n before encoding and sending.
        :return: None
        :rtype: None
        """
        if not self._socket:
            raise OSError("Not connected")

        line_bytes = line.encode(self._encoding)
        max_line_length = 510 # 512 bytes total minus \r\n

        if len(line_bytes) <= max_line_length:
            lines_to_send = [line_bytes]
        else:
            split_index = line_bytes.find(b':')
            prefix_bytes = line_bytes[:split_index + 1] # include ':'
            msg_bytes = line_bytes[split_index + 1:]
            slice_size = max_line_length - len(prefix_bytes)
            slices = self._slice_by_bytes(msg_bytes, slice_size=slice_size)
            lines_to_send = [prefix_bytes + slice for slice in slices]

        for l in lines_to_send:
            self._socket.sendall(l + b'\r\n')

    @staticmethod
    def _slice_by_bytes(line_bytes, slice_size=512):
        """Split line_bytes into slices of a specified byte size, ensuring that
        multi-byte characters are not split in the middle.

        :param bytes line_bytes: The line to slice, already encoded as bytes.
        :param int slice_size: The maximum byte size of each slice. Defaults to
            512 bytes, which is a common limit for IRC messages.
        :return: A list of byte strings, each representing a slice of the
            original bytes line.
        :rtype: list[bytes]
        """
        slices = []
        start = 0
        encoded_size = len(line_bytes)
        bit_mask = 0b11000000

        while start < encoded_size:
            end = min(start + slice_size, encoded_size)
            while start < end < encoded_size:
                if (line_bytes[end] & bit_mask) == 0b10000000:
                    end -= 1
                else:
                    break
            slices.append(line_bytes[start:end])
            start = end
        return slices
