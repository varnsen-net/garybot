"""Uses gevent to define three actors: a listener, a dispatcher, and a writer. The listener sits on the raw TCP socket and does one thing: reads lines from the server and puts them onto a queue — its outbox.

The dispatcher receives raw IRC lines from the reader, parses them (:nick!user@host PRIVMSG #channel :hello), and then decides what to do. For most messages it does nothing, but for commands it might spawn a new short-lived greenlet to handle that command and put a response onto the writer's inbox.

The writer just sits on its inbox queue and drains it to the socket.
"""
import time
import socket
import ssl
import re
from collections import namedtuple

import gevent
from gevent.queue import Queue, Empty
from gevent.pool import Pool
from loguru import logger

from src.client.logger import irc_logger
import src.channel_functions.functions as channel_functions


_EXIT_CODE = "goodnight"


class Listener(gevent.Greenlet):

    _BUFFER_SIZE = 4096

    def __init__(self, outbox, socket, stop_event, encoding='utf-8'):
        gevent.Greenlet.__init__(self)
        self.outbox = outbox
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
        logger.info("Listening...")
        while not self._stop_event.is_set():
            try:
                for line in self._recv_lines():
                    line = line.strip()
                    if line:
                        self.outbox.put(line)
            except OSError as e:
                if not self._stop_event.is_set():
                    logger.error(f"Listener error: {e}")
                    raise
                break


class Dispatcher(gevent.Greenlet):

    # matches user-originated messages: `:nick!ident@host COMMAND target :message`
    _USER_MSG_RE = re.compile(r":(\S+!\S+@\S+) ([A-Z]+) (\S+) :(.*)")
    # matches server PING: `PING :server`
    _PING_RE = re.compile(r"^PING :(.+)$")
    _IMAGINE_REGEX = re.compile(r"^imagine unironically")
    _REASON_REGEX = re.compile(r"\breason\b")

    ParsedMessage = namedtuple("ParsedMessage", [
        "nick", "ident", "host", "command", "target", "message",
        "word_list", "word_count", "timestamp",
    ])

    def __init__(self,
                 outbox,
                 nick,
                 admin_nick,
                 main_channel,
                 ignore_list,
                 user_logs_path,
                 stop_event):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self.outbox = outbox
        self.nick = nick
        self.admin_nick = admin_nick
        self.main_channel = main_channel
        self.ignore_list = ignore_list
        self.user_logs_path = user_logs_path
        self._pool = Pool(10)
        self._running = False
        self._stop_event = stop_event

    def _dispatch(self, line):
        """"""
        logger.debug(f"< {line}")

        # ping pong
        ping_match = self._PING_RE.match(line)
        if ping_match:
            server = ping_match.group(1)
            self.outbox.put(f"PONG :{server}")
            return

        # rejoin if kicked
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "KICK" and parts[2] == self.main_channel:
            kicked_nick = parts[3]
            if kicked_nick.lower() == self.nick.lower():
                logger.warning(f"Kicked from {self.main_channel} — rejoining...")
                gevent.sleep(2)
                self.outbox.put(f"JOIN {self.main_channel}")
            return

        # parse user message
        timestamp = time.time()
        parsed = self._parse_raw_msg(line, timestamp)
        if parsed is None:
            return   # server notice, MODE, etc.

        # quit on admin exit code
        if (
            parsed.command == "PRIVMSG"
            and parsed.nick
            and parsed.nick.lower() == self.admin_nick.lower()
            and parsed.message == _EXIT_CODE
        ):
            logger.info(f"Exit code received from {parsed.nick}. Shutting down.")
            self._stop_event.set()
            return

        # filter out messages we don't care about
        if not self._should_dispatch(parsed):
            return

        # dispatch to handler
        try:
            self._pool.spawn(
                irc_logger,
                parsed.nick,
                parsed.target,
                parsed.message,
                parsed.timestamp,
                self.user_logs_path,
            )
            if self._IMAGINE_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.imagine_without_iron,
                    parsed.target,
                    parsed.message
                )
            if self._REASON_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.reason_will_prevail,
                    parsed.target
                )
            if parsed.message.startswith(self.nick):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.respond_to_mention,
                    parsed.target,
                    parsed.message
                )
            if parsed.message.startswith(".spaghetti"):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_spaghetti,
                    parsed.target,
                )
            if parsed.message.startswith(".ask"):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_ask,
                    parsed.target,
                    parsed,
                    self.user_logs_path,
                )
        except Exception as exc: # never let a bad handler kill the loop
            logger.exception(f"Handler raised an exception: {exc}")

    def _parse_raw_msg(self, raw, timestamp):
        """Parse a raw IRC line into a ParsedMessage.

        Returns None when the line doesn't match the user-message pattern
        (server notices, MODE lines, etc.) so callers can skip them cleanly.

        :param str raw: The raw IRC line to parse.
        :param float timestamp: The time the message was received (e.g. time.time()).
        :return: ParsedMessage if the line matches a user message, or None otherwise.
        :rtype: ParsedMessage | None
        """
        m = self._USER_MSG_RE.match(raw)
        if not m:
            return None

        prefix, command, target, message = m.group(1, 2, 3, 4)
        nick, rest = prefix.split("!", 1)
        ident, host = rest.split("@", 1) if "@" in rest else (rest, "")

        words = [w for w in message.split() if w] # collapse multiple spaces
        return self.ParsedMessage(
            nick=nick,
            ident=ident,
            host=host,
            command=command,
            target=target,
            message=message,
            word_list=words,
            word_count=len(words),
            timestamp=timestamp,
        )

    def _should_dispatch(self, msg):
        """Return True only when a message is worth passing to the handler.

        Rules (all must pass):
        1. Must be a PRIVMSG.
        2. Must originate from a real user (nick and ident present).
        3. Nick must not be on the ignore list.
        4. Target must be one of the bot's channels.

        :param ParsedMessage msg: The message to evaluate.
        :return: True if the message should be dispatched to the handler,
            False otherwise.
        :rtype: bool
        """
        if msg.command != "PRIVMSG":
            return False
        if not msg.nick or not msg.ident:
            return False
        if msg.nick.lower() in self.ignore_list:
            return False
        if msg.target not in self.main_channel:
            return False
        return True

    def _run_function(self, func, target, *args, **kwargs):
        """"""
        try:
            response = func(*args, **kwargs)
            if response:
                self.outbox.put(f"PRIVMSG {target} :{response}")
        except Exception as e:
            logger.exception(f"Error in handler function: {e}")
            self.outbox.put(f"PRIVMSG {target} :Sorry, an error occurred while processing your request.")

    def _run(self):
        """"""
        while not self._stop_event.is_set():
            try:
                line = self.inbox.get(timeout=1)
            except Empty:
                continue
            self._dispatch(line)


class Writer(gevent.Greenlet):

    def __init__(self, socket, stop_event, encoding='utf-8'):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._socket = socket
        self._encoding = encoding
        self._running = False
        self._stop_event = stop_event

    def _send(self, line):
        """Encode and send a single IRC line (newline appended automatically)."""
        if not self._socket:
            raise OSError("Not connected")
        raw = (line + "\r\n").encode(self._encoding)
        try:
            self._socket.sendall(raw)
        except (OSError, ssl.SSLError) as exc:
            logger.error(f"Send failed: {exc}")
            raise

    def _run(self):
        """"""
        while not self._stop_event.is_set():
            try:
                line = self.inbox.get(timeout=1)
            except Empty:
                continue
            self._send(line)
