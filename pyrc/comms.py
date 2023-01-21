import os
import ssl
import time
import socket


# connection environment variables
_SERVER = os.getenv('SERVER')
_SSLPORT = os.getenv('SSLPORT')
_BOT_NICK = os.getenv('BOT_NICK')
_ADMIN_NICK = os.getenv('ADMIN_NICK')
_ADMIN_IDENT = os.getenv('ADMIN_IDENT')
_MAIN_CHANNEL = os.getenv('MAIN_CHANNEL')
_GAME_CHANNEL = os.getenv('GAME_CHANNEL')
_EXIT_CODE = os.getenv('EXIT_CODE')
_IGNORE_LIST = os.getenv('IGNORE_LIST')


class irc_socket():
    """A class to handle the socket connection to the IRC server.

    Attributes:
        context: An SSL context object.
        sock: A socket object.
        sslsock: A socket object wrapped in an SSL context.
    """
    def __init__(self):
        """Initialize the socket connection to the IRC server."""
        self.context = ssl.create_default_context()
        self.sock = socket.create_connection((_SERVER, _SSLPORT))
        self.sslsock = self.context.wrap_socket(self.sock, server_hostname=_SERVER)
        return


# socket connection
_IRCSOCK = irc_socket()


# functions
def send_bytes(message, ircsock=_IRCSOCK):
    """Encode string and send to server.
    
    :param str message: The message to send to the server.
    :param sslsocket ircsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    b = bytes(f"{message}\r\n", "UTF-8")
    ircsock.sslsock.send(b)
    return
        

def send_message(message, nick=None, target=_MAIN_CHANNEL):
    """Encode string and send to channel or nick.
    
    :param str message: The message to send to the target.
    :param str nick: The nick to send the message @.
    :param str target: The channel or nick to send the message to.
    :return: None
    :rtype: None
    """
    if nick:
        message = f"{nick}: {message}"
    send_bytes(f"PRIVMSG {target} :{message}")
    return


def ping_pong(raw_msg):
    """Send a pong reply when pinged by the server.
    
    :param str raw_msg: The raw message received from the server.
    :return: None
    :rtype: None
    """
    if raw_msg.startswith("PING"):
        originating_server = raw_msg.split(' ', 1)[1]
        send_bytes(f"PONG {originating_server}")
    return


def connect_to_server(server=_SERVER, sslport=_SSLPORT, bot_nick=_BOT_NICK,
                      main_channel=_MAIN_CHANNEL):
    """Connect to the IRC server.

    :param str server: The server to connect to.
    :param str sslport: The port to connect to.
    :param str bot_nick: The bot's nick.
    :param str main_channel: The main channel to join.
    :return: None
    :rtype: None
    """
    # TODO put this in a try loop that exits after n attempts to connect
    time.sleep(1)
    send_bytes(f"NICK {bot_nick}")
    time.sleep(1)
    send_bytes(f"USER {bot_nick} 0 * :{bot_nick}")
    time.sleep(1)
    send_bytes(f"JOIN {main_channel}")
    return


def disconnect(admin_nick=_ADMIN_NICK, ircsock=_IRCSOCK):
    """Send a goodbye message to the admin and disconnects from the server.

    :param str admin_nick: The admin's nick.
    :param sslsocket ircsock: The SSL socket to disconnect.
    :return: None
    :rtype: None
    """
    send_message("Goodnight!", target=admin_nick)
    ircsock.sslsock.shutdown(2)
    ircsock.sslsock.close()
    return


def listen_for_msg(ircsock=_IRCSOCK):
    """Listen for messages from the IRC server.
    
    :param sslsocket ircsock: The SSL socket to listen on.
    :return: The raw message received from the server.
    :rtype: str
    """
    raw_msg = ircsock.sslsock.recv(4096).decode("UTF-8",errors='replace').strip("\r\n")
    return raw_msg


def reconnect_if_disconnected(raw_msg:str, ircsock=_IRCSOCK) -> None:
    """Reconnect to the server if the connection is lost.

    :param str raw_msg: The raw message received from the server.
    :param sslsocket ircsock: The SSL socket currently in use.
    :return: None
    :rtype: None
    """
    if len(raw_msg) == 0:
        ircsock.sslsock.shutdown(2)
        ircsock.sslsock.close()
        time.sleep(2)
        ircsock.sock = socket.create_connection((_SERVER, _SSLPORT))
        ircsock.sslsock = ircsock.context.wrap_socket(ircsock.sock, server_hostname=_SERVER)
        connect_to_server()
    return


def rejoin_if_kicked(raw_msg, main_channel=_MAIN_CHANNEL,
                     bot_nick=_BOT_NICK):
    """Rejoin the channel if kicked.

    :param str raw_msg: The raw message received from the server.
    :param str main_channel: The main channel to join.
    :param str bot_nick: The bot's nick.
    :return: None
    :rtype: None
    """
    if f"KICK {main_channel} {bot_nick} :" in raw_msg:
        time.sleep(2)
        send_bytes(f"JOIN {main_channel}")
        send_message("rude")
    return


def received_exit_code(message_payload, bot_nick=_BOT_NICK,
                       admin_nick=_ADMIN_NICK):
    """Check if message is an exit code from the admin.

    :param dict message_payload: The message payload parsed from the raw message.
    :param str bot_nick: The bot's nick.
    :param str admin_nick: The admin's nick.
    :return: True if the bot gets a valid exit condition, False otherwise
    :rtype: bool
    """
    exit_condition = (
        message_payload['target'] == bot_nick and
        message_payload['nick'] == admin_nick and
        message_payload['message'] == "goodnight"
    )
    return exit_condition


def message_is_valid(message_payload, ignore_list=_IGNORE_LIST,
                     main_channel=_MAIN_CHANNEL):
    """Check if message should be ignored or not.

    :param dict message_payload: The message payload parsed from the raw message.
    :param str ignore_list: The list of nicks to ignore.
    :param str main_channel: The main channel the bot lurks in.
    :return: True if the message should be considered, False otherwise.
    :rtype: bool
    """
    valid_msg_condition = (
        message_payload['nick'] != None and
        message_payload['nick'] not in ignore_list and
        message_payload['target'] == main_channel and 
        message_payload['command'] == 'PRIVMSG' and
        message_payload['word_count'] > 0
    )
    return valid_msg_condition




