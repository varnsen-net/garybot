"""Uses gevent to define three actors: a listener, a dispatcher, and a writer. The listener sits on the raw TCP socket and does one thing: reads lines from the server and puts them onto a queue — its outbox.

The dispatcher receives raw IRC lines from the reader, parses them (:nick!user@host PRIVMSG #channel :hello), and then decides what to do. For most messages it does nothing, but for commands it might spawn a new short-lived greenlet to handle that command and put a response onto the writer's inbox.

The writer just sits on its inbox queue and drains it to the socket.
"""
import time
import re
from collections import namedtuple

import gevent
from gevent.queue import Queue, Empty
from gevent.pool import Pool
from loguru import logger

import src.channel_functions.functions as channel_functions



class Dispatcher(gevent.Greenlet):
    """The Dispatcher receives raw IRC lines from the reader, parses them
    (:nick!user@host PRIVMSG #channel :hello), and then decides what to do. For
    most messages it does nothing, but for commands it might spawn a new
    short-lived greenlet to handle that command and put a response onto the
    writer's inbox.

    Attributes:
        inbox (Queue): A gevent Queue where raw IRC lines are received from the
            reader.
        nick (str): The bot's own nickname, used for command parsing.
        main_channel (str): The channel the bot is active in, used for filtering
            messages and sending responses.
        admin_nick (str): The nickname of the admin user, whose messages can
            trigger a shutdown when they contain the exit code.
        ignore_list (set[str]): A set of lowercase nicknames to ignore.
        _pool (Pool): A gevent Pool for running handler functions concurrently.
        _stop_event (Event): A gevent Event that signals the dispatcher to stop.
        _app_config (AppConfig): The application configuration object.
        _writer (Writer): A reference to the Writer actor, used to send responses
            back to the server.
        _logger (Logger): A logger for logging messages and errors.
        _EXIT_CODE (str): A special message that, when received from the admin user,
            will trigger a shutdown of the dispatcher.
        _USER_MSG_RE (Pattern): A regular expression pattern for parsing user-originated
            messages in the format `:nick!ident@host COMMAND target :message`.
        _PING_RE (Pattern): A regular expression pattern for matching PING messages
            from the server.
        _IMAGINE_REGEX (Pattern): A regular expression pattern for detecting messages
            that begin with the phrase "imagine unironically".
        _REASON_REGEX (Pattern): A regular expression pattern for detecting messages
            that contain the word "reason".
        _DOT_ASK_REGEX (Pattern): A regular expression pattern for matching messages
            that start with the command ".ask" followed by some text.
        ParsedMessage (namedtuple): A named tuple class for representing parsed user messages,
            with fields for nick, ident, host, command, target, message, word_list,
            word_count, and timestamp.
    """

    _EXIT_CODE = "goodnight"
    _USER_MSG_RE = re.compile(r":(\S+!\S+@\S+) ([A-Z]+) (\S+) :(.*)") # `:nick!ident@host COMMAND target :message`
    _PING_RE = re.compile(r"^PING :(.+)$")
    _IMAGINE_REGEX = re.compile(r"^imagine unironically\b")
    _REASON_REGEX = re.compile(r"\breason\b")
    _DOT_ASK_REGEX = re.compile(r"^\.ask\s+(.+)")
    _DOT_WA_REGEX = re.compile(r"^\.wa\s+(.+)")
    _DOT_APOD_REGEX = re.compile(r"^\.apod\b")
    _DOT_TRIVIA_REGEX = re.compile(r"^\.tr(ivia)?(\s*[AaBbCcDd]+)?")

    ParsedMessage = namedtuple("ParsedMessage", [
        "nick", "ident", "host", "command", "target", "message",
        "word_list", "word_count", "timestamp",
    ])

    def __init__(self,
                 writer,
                 logger,
                 trivia,
                 stop_event,
                 app_config):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self.nick = app_config.irc_nick
        self.main_channel = app_config.irc_main_channel
        self.admin_nick = app_config.irc_admin_nick
        self.ignore_list = {n.lower().strip() for n in app_config.irc_ignore_list.split(",") if n.strip()}
        self.current_convo = []

        self._pool = Pool(10)
        self._stop_event = stop_event
        self._app_config = app_config
        self._writer = writer
        self._logger = logger
        self._trivia = trivia

    def _dispatch(self, line):
        """Dispatch a raw IRC line received from the reader.

        :param str line: The raw IRC line to dispatch.
        :return: None
        :rtype: None
        """

        # ping pong
        ping_match = self._PING_RE.match(line)
        if ping_match:
            server = ping_match.group(1)
            self._writer.inbox.put(f"PONG :{server}")
            return

        # rejoin if kicked
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "KICK" and parts[2] == self.main_channel:
            kicked_nick = parts[3]
            if kicked_nick.lower() == self.nick.lower():
                logger.warning(f"Kicked from {self.main_channel} — rejoining...")
                gevent.sleep(2)
                self._writer.inbox.put(f"JOIN {self.main_channel}")
            return

        # parse user message
        timestamp = time.time()
        parsed = self._parse_raw_msg(line, timestamp)
        if parsed is None:
            return   # server notice, MODE, etc.

        # update current conversation
        self._update_current_convo(parsed.nick, parsed.message)

        # quit on admin exit code
        if (
            parsed.command == "PRIVMSG"
            and parsed.nick
            and parsed.nick.lower() == self.admin_nick.lower()
            and parsed.message == self._EXIT_CODE
        ):
            logger.info(f"Exit code received from {parsed.nick}. Shutting down.")
            self._stop_event.set()
            return

        # filter out messages we don't care about
        if not self._should_dispatch(parsed):
            return

        # log message
        if not parsed.message.startswith((".", ",", "!")):
            self._logger.inbox.put(parsed)

        # dispatch to handler
        try:
            if self._IMAGINE_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.imagine_without_iron,
                    parsed.message,
                )
            if self._REASON_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.reason_will_prevail,
                )
            if parsed.message.startswith(".spaghetti"):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_spaghetti,
                )
            if self._DOT_ASK_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_ask,
                    parsed.word_list[1],
                    parsed.target,
                    self._app_config.user_logs_path,
                )
            if self._DOT_WA_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_wolfram,
                    parsed.nick,
                    parsed.message,
                    self._app_config.wolfram_api_key.get_secret_value(),
                )
            if self._DOT_APOD_REGEX.search(parsed.message):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_apod,
                    parsed.nick,
                    self._app_config.nasa_api_key.get_secret_value(),
                )
            if parsed.message.startswith(self.nick):
                self._pool.spawn(
                    self._run_function,
                    channel_functions.dot_arb,
                    parsed.nick,
                    parsed.message,
                    self._app_config.llm_api_key.get_secret_value(),
                    self._app_config.irc_llm_model,
                    "\n".join(self.current_convo),
                    self._app_config.project_root,
                    self.nick,
                )
            if match := self._DOT_TRIVIA_REGEX.search(parsed.message):
                self._trivia.inbox.put((parsed.nick, match))
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

        words = [w for w in message.split() if w]
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

    def _update_current_convo(self, nick, message):
        """"""
        self.current_convo.append(f"<{nick}>: {message}")
        self.current_convo = self.current_convo[-50:]

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
        if msg.target != self.main_channel:
            return False
        return True

    def _run_function(self, func, *args, **kwargs):
        """Run a handler function and put its response onto the writer's inbox.

        This method is a wrapper around handler functions to catch exceptions and
        ensure that any errors are logged and a user-friendly message is sent back
        to the channel instead of crashing the dispatcher.

        :param callable func: The handler function to run.
        :param args: Positional arguments to pass to the handler function.
        :param kwargs: Keyword arguments to pass to the handler function.
        :return: None
        :rtype: None
        """
        try:
            response = func(*args, **kwargs)
            if response:
                self._update_current_convo(self.nick, response)
                self._writer.inbox.put(f"PRIVMSG {self.main_channel} :{response}")
        except Exception as e:
            logger.exception(f"Error in handler function: {e}")
            self._writer.inbox.put(f"PRIVMSG {self.main_channel} :Sorry, an error occurred while processing your request.")

    def _run(self):
        """The main loop of the dispatcher greenlet. Continuously reads lines
        from the inbox and dispatches them until the stop event is set.

        :return: None
        :rtype: None
        """
        logger.info("Dispatcher started.")
        while not self._stop_event.is_set():
            try:
                line = self.inbox.get(timeout=1)
            except Empty:
                continue
            try:
                self._dispatch(line)
            except Exception as e:
                logger.exception(f"Error dispatching line: {line}\nException: {e}")
