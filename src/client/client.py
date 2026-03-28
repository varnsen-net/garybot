"""
SSL IRC client for a bot.

Usage:
    client = IRCClient(app_config)
    client.start()

Uses gevent to handle three actors: a listener, a dispatcher, and a writer. The listener sits on the raw TCP socket and does one thing: reads lines from the server and puts them onto a queue — its outbox.

The dispatcher receives raw IRC lines from the reader, parses them (:nick!user@host PRIVMSG #channel :hello), and then decides what to do. For most messages it does nothing, but for commands it might spawn a new short-lived greenlet to handle that command and put a response onto the writer's inbox.

The writer just sits on its inbox queue and drains it to the socket.
"""

from loguru import logger
import re
import socket
import ssl
import time
from dataclasses import dataclass, field

import gevent
from gevent.queue import Queue
from gevent.pool import Pool

from src.client.actors import Listener, Dispatcher, Writer
from src.client.logger import Logger


class IRCClient:
    """
    SSL IRC client designed for a single-bot deployment.

    Parameters
    ----------
    app_config : AppConfig
        Application configuration object containing necessary settings like server, port, nick, and main channel.
    """

    _RECV_TIMEOUT = 5.0

    def __init__(self, app_config):
        self.server = app_config.irc_server
        self.port = int(app_config.irc_port)
        self.nick = app_config.irc_nick # bot's own nick
        self.main_channel = app_config.irc_main_channel

        self._sock: "ssl.SSLSocket | None" = None
        self._stop_event = gevent.event.Event()
        self._app_config = app_config

    def start(self):
        """Connect and start the main listen loop, reconnecting as needed."""
        self._connect()
        gevent.sleep(1) # small delay to ensure connection is fully established
        self._writer = Writer(
            self._sock,
            self._stop_event,
        )
        self._logger = Logger(
            self._stop_event,
            self._app_config,
        )
        self._dispatcher = Dispatcher(
            self._writer,
            self._logger,
            self._stop_event,
            self._app_config,
        )
        self._listener = Listener(
            self._dispatcher,
            self._sock,
            self._stop_event,
        )
        self._writer.start()
        self._logger.start()
        self._dispatcher.start()
        self._listener.start()
        gevent.joinall([
            self._writer,
            self._logger,
            self._dispatcher,
            self._listener,
        ])
        self._disconnect()

    def _connect(self):
        """Open a TLS socket and register with the server."""
        logger.info(f"Connecting to {self.server}:{self.port}...")
        self._stop_event.clear()
        raw_sock = socket.create_connection((self.server, self.port), timeout=30)
        ctx = ssl.create_default_context()
        self._sock = ctx.wrap_socket(raw_sock, server_hostname=self.server)
        self._sock.settimeout(self._RECV_TIMEOUT)

        # IRC registration
        # move this elsewhere
        self._sock.sendall((f"NICK {self.nick}" + "\r\n").encode('utf-8'))
        self._sock.sendall((f"USER {self.nick} 0 * :{self.nick}" + "\r\n").encode('utf-8'))
        logger.info(f"Registered as {self.nick}")
        self._sock.sendall((f"JOIN {self.main_channel}" + "\r\n").encode('utf-8'))

    def _disconnect(self):
        """"""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

