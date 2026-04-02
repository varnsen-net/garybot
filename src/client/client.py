"""
SSL IRC client for a bot.

Usage:
    client = IRCClient(app_config)
    client.start()

Uses gevent to handle four actors: a listener that reads from the socket, a dispatcher that processes messages and generates responses, a logger that logs messages to disk, and a writer that sends messages to the server.

The writer just sits on its inbox queue and drains it to the socket.
"""
import socket
import ssl

import gevent
from loguru import logger

from src.actors.build import build_actors


class IRCClient:
    """
    SSL IRC client designed for a single-bot deployment.

    Attributes:
        server (str): IRC server hostname or IP address.
        port (int): IRC server port number.
        nick (str): Bot's nickname on the server.
        main_channel (str): Main channel to join on startup.
        _sock (ssl.SSLSocket | None): SSL socket for communication with the server.
        _stop_event (gevent.event.Event): Event to signal threads to stop.
        _app_config: Configuration object containing app settings.
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
        logger.info("Starting actors...")
        actors = build_actors(self._sock, self._stop_event, self._app_config)
        for actor in actors:
            actor.start()
        gevent.joinall(actors, raise_error=True)
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
        """Close the socket and clean up resources."""
        if self._sock:
            try:
                logger.info("Closing socket...")
                self._sock.close()
            except OSError:
                pass
            self._sock = None
