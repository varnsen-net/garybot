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


# create a socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sslsock = ssl.wrap_socket(socket)


def send_bytes(message, sslsock=sslsock):
    """Encode string and send to server.
    
    :param str message: The message to send to the server.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    b = bytes(f"{message}\r\n", "UTF-8")
    sslsock.send(b)
    return
        

def send_message(message, target=_MAIN_CHANNEL, sslsock=sslsock):
    """Encode string and send to channel or nick.
    
    :param str message: The message to send to the target.
    :param str target: The channel or nick to send the message to.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    send_bytes(f"PRIVMSG {target} :{message}")
    return


def ping_pong(raw_msg, sslsock=sslsock):
    """Send a pong reply when pinged by the server.
    
    :param str raw_msg: The raw message received from the server.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    if raw_msg.startswith("PING"):
        originating_server = raw_msg.split(' ', 1)[1]
        send_bytes(f"PONG {originating_server}")
    return


def connect_to_server(server=_SERVER, sslport=_SSLPORT, bot_nick=_BOT_NICK,
                      main_channel=_MAIN_CHANNEL, sslsock=sslsock):
    """Connect to the IRC server.

    :param str server: The server to connect to.
    :param str sslport: The port to connect to.
    :param str bot_nick: The bot's nick.
    :param str main_channel: The main channel to join.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    sslport = int(sslport)
    # TODO put this in a try loop that exits after n attempts to connect
    sslsock.connect((server, sslport))
    time.sleep(1)
    send_bytes(f"NICK {bot_nick}")
    time.sleep(1)
    send_bytes(f"USER {bot_nick} 0 * :{bot_nick}")
    time.sleep(1)
    send_bytes(f"JOIN {main_channel}")
    return


def disconnect(admin_nick=_ADMIN_NICK, sslsock=sslsock):
    """Send a goodbye message to the admin and disconnects from the server.

    :param str admin_nick: The admin's nick.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    send_message("Goodnight!", admin_nick)
    sslsock.shutdown(2)
    sslsock.close()
    return


def listen_for_msg(sslsock=sslsock):
    """Listen for messages from the IRC server.
    
    :param sslsocket sslsock: The SSL socket to listen on.
    :return: None
    :rtype: None
    """
    raw_msg = sslsock.recv(4096).decode("UTF-8",errors='replace').strip("\r\n")
    return raw_msg


def reconnect_if_disconnected(raw_msg:str, sslsock=sslsock) -> None:
    """Reconnect to the server if the connection is lost.

    :param str raw_msg: The raw message received from the server.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    if len(raw_msg) == 0:
        time.sleep(2)
        connect_to_server(sslsock)
    return


def rejoin_if_kicked(raw_msg, main_channel=_MAIN_CHANNEL,
                     bot_nick=_BOT_NICK, sslsock=sslsock):
    """Rejoin the channel if kicked.

    :param str raw_msg: The raw message received from the server.
    :param str main_channel: The main channel to join.
    :param str bot_nick: The bot's nick.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: None
    :rtype: None
    """
    if f"KICK {main_channel} {bot_nick} :" in raw_msg:
        time.sleep(2)
        send_bytes(f"JOIN {main_channel}")
        send_message("rude")
    return


def received_exit_code(target, nick, message, bot_nick=_BOT_NICK,
                       admin_nick=_ADMIN_NICK, sslsock=sslsock):
    """Check if message is an exit code from the admin.

    :param str target: The channel or nick the message was sent to.
    :param str nick: The nick the message was sent from.
    :param str message: The message received.
    :param str bot_nick: The bot's nick.
    :param str admin_nick: The admin's nick.
    :param sslsocket sslsock: The SSL socket to send the message through.
    :return: True if the bot gets a valid exit condition, False otherwise
    :rtype: bool
    """
    exit_condition = (
        target == bot_nick and
        nick == admin_nick and
        message == "goodnight"
    )
    return exit_condition


def message_is_valid(target, word_count, nick, command, ignore_list=_IGNORE_LIST,
                     main_channel=_MAIN_CHANNEL):
    """Check if message should be ignored or not.

    :param str target: The channel or nick the message was sent to.
    :param int word_count: The number of words in the message.
    :param str nick: The nick the message was sent from.
    :param str command: The IRC command preceeding the user message.
    :param str ignore_list: The list of nicks to ignore.
    :param str main_channel: The main channel the bot lurks in.
    :return: True if the message should be considered, False otherwise.
    :rtype: bool
    """
    valid_msg_condition = (
        nick != None and
        nick not in ignore_list and
        target == main_channel and 
        command == 'PRIVMSG' and
        word_count > 0
    )
    return valid_msg_condition




