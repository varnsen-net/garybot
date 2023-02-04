import os
import ssl
import time
import socket


class irc_client():
    """
    Creates a client object for communicating with an IRC server.

    Attributes
    ----------
    context : ssl.SSLContext
        SSL default context.
    server : str
        The server to connect to.
    sslport : int
        The port to connect through.
    admin_nick : str
        The bot admin's IRC nick.
    admin_ident : str
        The bot admin's IRC ident.
    exit_code : str
        The exit code to send to the bot to shut it down.
    ignore_list : list
        A list of nicks to ignore.
    bot_nick : str
        The bot's IRC nick.
    main_channel : str
        The main channel to join.
    game_channel : str
        The game channel to join.
    sock : socket.socket
        The socket connection.
    sslsock : ssl.SSLSocket
        The SSL-wrapped socket.
    """
    def __init__(self):
        """Initialize the client."""
        self.context = ssl.create_default_context()
        self.server = os.getenv('SERVER')
        self.sslport = os.getenv('SSLPORT')
        self.admin_nick = os.getenv('ADMIN_NICK')
        self.admin_ident = os.getenv('ADMIN_IDENT')
        self.exit_code = os.getenv('EXIT_CODE')
        self.ignore_list = os.getenv('IGNORE_LIST')
        self.bot_nick = os.getenv('BOT_NICK')
        self.main_channel = os.getenv('MAIN_CHANNEL')
        self.game_channel = os.getenv('GAME_CHANNEL')
        return


    def close_existing_socket(self):
        """
        Send a goodbye message to the admin and disconnect from the server.

        :return: None
        :rtype: None
        """
        if hasattr(self, 'sslsock'):
            self.sslsock.shutdown(2)
            self.sslsock.close()
        return


    def connect_to_server(self):
        """
        Connect to the IRC server.

        :return: None
        :rtype: None
        """
        # TODO create a function to close existing socket connections
        server = self.server
        sslport = self.sslport
        while True:
            self.close_existing_socket()
            try:
                self.sock = socket.create_connection((server, sslport))
                self.sslsock = self.context.wrap_socket(self.sock,
                                                        server_hostname=server)
                break
            except Exception:
                time.sleep(6)
        return


    def send_bytes(self, message):
        """
        Encode string and send to server.
        
        :param str message: The message to send to the server.
        :return: None
        :rtype: None
        """
        b = bytes(f"{message}\r\n", "UTF-8")
        self.sslsock.send(b)
        return
        

    def send_message(self, message, nick=None, target=None):
        """
        Send a message to a channel or nick.
        
        :param str message: The message to send to the target.
        :param str nick: The nick to send the message @.
        :param str target: The channel or nick to send the message to.
        :return: None
        :rtype: None
        """
        if nick:
            message = f"{nick}: {message}"
        if not target:
            target = self.main_channel
        self.send_bytes(f"PRIVMSG {target} :{message}")
        return


    def ping_pong(self, raw_msg):
        """
        Send a pong reply when pinged by the server.
        
        :param str raw_msg: The raw message received from the server.
        :return: None
        :rtype: None
        """
        if raw_msg.startswith("PING"):
            originating_server = raw_msg.split(' ', 1)[1]
            self.send_bytes(f"PONG {originating_server}")
        return


    def join_channel(self):
        """
        Register and join the main channel.

        :return: None
        :rtype: None
        """
        self.send_bytes(f"NICK {self.bot_nick}")
        self.send_bytes(f"USER {self.bot_nick} 0 * :{self.bot_nick}")
        self.send_bytes(f"JOIN {self.main_channel}")
        return


    def listen_for_msg(self):
        """
        Listen for messages from the IRC server.
        
        :return: The raw message received from the server.
        :rtype: str
        """
        raw_msg = self.sslsock.recv(4096)
        raw_msg = raw_msg.decode("UTF-8",errors='replace').strip("\r\n")
        return raw_msg


    def reconnect_if_disconnected(self, raw_msg):
        """
        Reconnect to the server if the connection is lost.

        :param str raw_msg: The raw message received from the server.
        :return: None
        :rtype: None
        """
        if len(raw_msg) == 0:
            self.connect_to_server()
            self.join_channel()
        return


    def rejoin_if_kicked(self, raw_msg):
        """
        Rejoin the channel if kicked.

        :param str raw_msg: The raw message received from the server.
        :return: None
        :rtype: None
        """
        if raw_msg.startswith(f"KICK {self.main_channel} {self.bot_nick} :"):
            time.sleep(2)
            self.send_bytes(f"JOIN {self.main_channel}")
            self.send_message("rude")
        return


    def received_exit_code(self, message_payload):
        """
        Check if message is an exit code from the admin.

        :param dict message_payload: The message payload parsed from the raw
            message.
        :return: True if the bot gets a valid exit condition, False otherwise
        :rtype: bool
        """
        exit_condition = (
            message_payload['target'] == self.bot_nick and
            message_payload['nick'] == self.admin_nick and
            message_payload['message'] == "goodnight"
        )
        return exit_condition


    def message_is_valid(self, message_payload):
        """
        Check if message should be ignored or not.

        :param dict message_payload: The message payload parsed from the raw
            message.
        :return: True if the message should be considered, False otherwise.
        :rtype: bool
        """
        valid_msg_condition = (
            message_payload['nick'] != None and
            message_payload['nick'] not in self.ignore_list and
            message_payload['target'] == self.main_channel and 
            message_payload['command'] == 'PRIVMSG' and
            message_payload['word_count'] > 0
        )
        return valid_msg_condition




