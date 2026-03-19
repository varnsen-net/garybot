"""
irc_client.py — SSL IRC client for a bot.

Usage:
    client = IRCClient(app_config, message_handler)
    client.start()
"""

from loguru import logger
import re
import socket
import ssl
import time
from dataclasses import dataclass, field

import src.channel_functions.functions as fun # these functions are FUN! :^)


# ---------------------------------------------------------------------------
# IRC message parsing
# ---------------------------------------------------------------------------

# Matches user-originated messages: `:nick!ident@host COMMAND target :message`
_USER_MSG_RE = re.compile(r":(\S+!\S+@\S+) ([A-Z]+) (\S+) :(.*)")

# Matches server PING: `PING :server`
_PING_RE = re.compile(r"^PING :(.+)$")


@dataclass
class ParsedMessage:
    """Structured representation of a parsed IRC message."""
    nick: str | None
    ident: str | None
    host: str | None
    command: str | None
    target: str | None
    message: str | None
    word_list: list[str] = field(default_factory=list)
    word_count: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_payload(self):
        """Return the dict your handler expects."""
        return {
            "nick": self.nick,
            "ident": self.ident,
            "target": self.target,
            "message": self.message,
            "command": self.command,
            "word_count": self.word_count,
            "word_list": self.word_list,
            "timestamp": self.timestamp,
        }


def parse_raw_msg(raw, timestamp):
    """Parse a raw IRC line into a ParsedMessage.

    Returns None when the line doesn't match the user-message pattern
    (server notices, MODE lines, etc.) so callers can skip them cleanly.

    :param str raw: The raw IRC line to parse.
    :param float timestamp: The time the message was received (e.g. time.time()).
    :return: ParsedMessage if the line matches a user message, or None otherwise.
    :rtype: ParsedMessage | None
    """
    m = _USER_MSG_RE.match(raw)
    if not m:
        return None

    prefix, command, target, message = m.group(1, 2, 3, 4)
    nick, rest = prefix.split("!", 1)
    ident, host = rest.split("@", 1) if "@" in rest else (rest, "")

    words = [w for w in message.split() if w] # collapse multiple spaces
    return ParsedMessage(
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


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class IRCClient:
    """
    SSL IRC client designed for a single-bot deployment.

    Parameters
    ----------
    app_config:
        Any object with the attributes described in __init__.
    reconnect_delay:
        Seconds to wait between reconnection attempts (default 30).
    max_reconnects:
        Maximum consecutive reconnection attempts before giving up
        (0 = unlimited, default 0).
    encoding:
        Line encoding used by the server (default 'utf-8', fallback 'latin-1').
    """

    # How long to block on recv() before looping again (seconds).
    _RECV_TIMEOUT = 300.0
    _BUFFER_SIZE = 4096

    def __init__(self,
                 app_config,
                 *,
                 reconnect_delay=30.0,
                 max_reconnects=0,
                 encoding="utf-8",):
        self.server = app_config.server
        self.port = int(app_config.port)
        self.nick = app_config.nick # bot's own nick
        self.admin_nick = app_config.admin_nick # bot admin's nick
        self.exit_code = app_config.exit_code
        self.main_channel = app_config.main_channel
        self.game_channel = app_config.game_channel

        raw_ignore = getattr(app_config, "ignore_list", "") or ""
        self.ignore_list = {
            n.lower().strip() for n in raw_ignore.split(",") if n.strip()
        }

        self._reconnect_delay = reconnect_delay
        self._max_reconnects = max_reconnects
        self._encoding = encoding

        self._sock: "ssl.SSLSocket | None" = None
        self._connected = False
        self._running = False
        self._recv_buffer = ""

        self._channels = [
            c for c in (self.main_channel, self.game_channel) if c
        ]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self):
        """Connect and start the main listen loop, reconnecting as needed."""
        self._running = True
        attempt = 0
        while self._running:
            try:
                self._connect()
                self._join_channels()
                attempt = 0           # reset on successful connection
                self._listen()
            except (OSError, ssl.SSLError) as exc:
                if not self._running:
                    break
                attempt += 1
                logger.warning(f"Connection error (attempt {attempt}): {exc}")
                if self._max_reconnects and attempt >= self._max_reconnects:
                    logger.error("Max reconnection attempts reached. Exiting.")
                    break
                logger.info(f"Reconnecting in {self._reconnect_delay} second(s)...")
                time.sleep(self._reconnect_delay)
            finally:
                self._disconnect()

    def stop(self):
        """Cleanly stop the client from outside the listen loop."""
        self._running = False
        self._disconnect()

    def send_msg(self, target, text):
        """Send a PRIVMSG to *target* (channel or nick)."""
        self._send(f"PRIVMSG {target} :{text}")

    def join(self, channel):
        """JOIN a channel."""
        self._send(f"JOIN {channel}")

    def part(self, channel, reason=""):
        """PART a channel."""
        self._send(f"PART {channel}" + (f" :{reason}" if reason else ""))

    def quit(self, reason=""):
        """Send QUIT and stop the client."""
        try:
            self._send("QUIT" + (f" :{reason}" if reason else ""))
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def _connect(self):
        """Open a TLS socket and register with the server."""
        logger.info(f"Connecting to {self.server}:{self.port}...")
        raw_sock = socket.create_connection((self.server, self.port), timeout=30)
        ctx = ssl.create_default_context()
        self._sock = ctx.wrap_socket(raw_sock, server_hostname=self.server)
        self._sock.settimeout(self._RECV_TIMEOUT)
        self._connected = True
        self._recv_buffer = ""

        # IRC registration
        self._send(f"NICK {self.nick}")
        self._send(f"USER {self.nick} 0 * :{self.nick}")
        logger.info(f"Registered as {self.nick}")

    def _disconnect(self):
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self._connected = False

    def _join_channels(self):
        for channel in self._channels:
            self.join(channel)
            logger.info(f"Joined {channel}")

    # ------------------------------------------------------------------
    # Low-level send / receive
    # ------------------------------------------------------------------

    def _send(self, line):
        """Encode and send a single IRC line (newline appended automatically)."""
        if not self._sock:
            raise OSError("Not connected")
        raw = (line + "\r\n").encode(self._encoding)
        try:
            self._sock.sendall(raw)
        except (OSError, ssl.SSLError) as exc:
            logger.error(f"Send failed: {exc}")
            raise

    def _recv_lines(self):
        """Read from the socket into a line buffer and return complete lines.

        Raises OSError on disconnect so the caller can trigger reconnection.
        """
        try:
            chunk = self._sock.recv(self._BUFFER_SIZE)
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

    # ------------------------------------------------------------------
    # Main listen loop
    # ------------------------------------------------------------------

    def _listen(self):
        """Process incoming lines until an error or clean shutdown."""
        logger.info("Listening...")
        while self._running:
            for line in self._recv_lines():
                line = line.strip()
                if line:
                    self._handle_raw(line)

    def _handle_raw(self, line):
        """Dispatch a single raw IRC line."""
        logger.debug(f"< {line}")

        # ping pong
        ping_match = _PING_RE.match(line)
        if ping_match:
            print(f"PONG :{ping_match.group(1)}")
            self._send(f"PONG :{ping_match.group(1)}")
            return

        # rejoin if kicked
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "KICK" and parts[2] in self._channels:
            kicked_nick = parts[3]
            if kicked_nick.lower() == self.nick.lower():
                channel = parts[2]
                logger.warning(f"Kicked from {channel} — rejoining...")
                time.sleep(2)
                self.join(channel)
            return

        # parse user message
        timestamp = time.time()
        parsed = parse_raw_msg(line, timestamp)
        if parsed is None:
            return   # server notice, MODE, etc.

        # quit on admin exit code
        if (
            parsed.command == "PRIVMSG"
            and parsed.nick
            and parsed.nick.lower() == self.admin_nick.lower()
            and parsed.message == self.exit_code
        ):
            logger.info(f"Exit code received from {parsed.nick}. Shutting down.")
            self.quit("Received exit code")
            return

        # filter out messages we don't care about
        if not self._should_dispatch(parsed):
            return

        # dispatch to handler
        try:
            # self.send_msg(parsed.target, f"Received your message: {parsed.message}")
            self._handle_payload(parsed)
        except Exception as exc:             # never let a bad handler kill the loop
            logger.exception(f"Handler raised an exception: {exc}")

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
        if msg.target not in self._channels:
            return False
        return True

    def _handle_payload(self, message_payload):
        """"""
        # regular expressions
        IMAGINE_REGEX = re.compile(r"^imagine unironically")
        REASON_REGEX = re.compile(r"\breason\b")

        trigger = message_payload.word_list[0]
        message = message_payload.message
        target = message_payload.target

        if IMAGINE_REGEX.search(message):
            self.send_msg(target, fun.imagine_without_iron(message))

        if REASON_REGEX.search(message):
            self.send_msg(target, fun.reason_will_prevail())

        # if message.startswith(irc_client.bot_nick):
            # run(fun.dot_arb, message_payload, irc_client, app_config)

        # match trigger:
            # case '.spaghetti':
                # run(fun.dot_spaghetti, message_payload, irc_client)
            # case '.ask':
                # run(fun.dot_ask, message_payload, irc_client)
            # case '.wa':
                # run(fun.dot_wolfram, message_payload, irc_client)
            # case '.apod':
                # run(fun.dot_apod, message_payload, irc_client)
            # case '.sb':
                # run(sportsbook.dot_sportsbook, message_payload, irc_client)

