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

    _RECV_TIMEOUT = 5.0

    def __init__(self,
                 app_config,
                 *,
                 reconnect_delay=30.0,
                 max_reconnects=5):
        self.server = app_config.irc_server
        self.port = int(app_config.irc_port)
        self.nick = app_config.irc_nick # bot's own nick
        self.main_channel = app_config.irc_main_channel
        self.admin_nick = app_config.irc_admin_nick # bot admin's nick for privileged commands
        self.ignore_list = app_config.irc_ignore_list
        self.llm_model = app_config.irc_llm_model
        # TODO: maybe just have fcns use env vars directly
        self.wolfram_api_key = app_config.wolfram_api_key
        self.odds_api_key = app_config.odds_api_key
        self.llm_api_key = app_config.llm_api_key

        self.project_root = app_config.project_root
        self.user_logs_path = app_config.user_logs_path

        raw_ignore = getattr(app_config, "ignore_list", "") or ""
        self.ignore_list = {
            n.lower().strip() for n in raw_ignore.split(",") if n.strip()
        }

        self._sock: "ssl.SSLSocket | None" = None
        self._stop_event = gevent.event.Event()

    def start(self):
        """Connect and start the main listen loop, reconnecting as needed."""
        self._connect()
        gevent.sleep(1) # small delay to ensure connection is fully established
        self._writer = Writer(self._sock, self._stop_event)
        self._dispatcher = Dispatcher(
            self._writer.inbox,
            self.nick,
            self.main_channel,
            self.admin_nick,
            self.ignore_list,
            self.llm_model,
            self.llm_api_key,
            self.project_root,
            self.user_logs_path,
            self._stop_event
        )
        self._listener = Listener(self._dispatcher.inbox, self._sock, self._stop_event)
        self._writer.start()
        self._dispatcher.start()
        self._listener.start()
        gevent.joinall([
            self._writer,
            self._dispatcher,
            self._listener
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

