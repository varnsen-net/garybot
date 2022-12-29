import ssl
import time
import socket
import traceback
import csv
from pyrc.constants import irc_config


# connection config
cconf = irc_config['Connection']


# create a socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sslsock = ssl.wrap_socket(socket)


def send_bytes(message:str, sslsock=sslsock) -> None:
    """Encode string and send to server."""
    b = bytes(f"{message}\r\n", "UTF-8")
    sslsock.send(b)
    return
        

def send_message(message:str, target:str=cconf['main_channel'],
                 sslsock=sslsock) -> None:
    """Encode string and send to channel or nick."""
    send_bytes(f"PRIVMSG {target} :{message}")
    return


def ping_pong(raw_msg:str, sslsock=sslsock) -> None:
    """Send a pong reply when pinged by the server."""
    if raw_msg.startswith("PING"):
        originating_server = raw_msg.split(' ', 1)[1]
        send_bytes(f"PONG {originating_server}")
    return


def connect_to_server(SERVER:str=cconf['server'], SSLPORT:int=cconf['sslport'],
                      BOT_NICK:int=cconf['bot_nick'],
                      MAIN_CHANNEL:str=cconf['main_channel'],
                      sslsock=sslsock) -> None:
    """Connect to the IRC server."""
    SSLPORT = int(SSLPORT)
    # TODO put this in a try loop that exits after n attempts to connect
    sslsock.connect((SERVER, SSLPORT))
    time.sleep(1)
    send_bytes(f"NICK {BOT_NICK}")
    time.sleep(1)
    send_bytes(f"USER {BOT_NICK} 0 * :{BOT_NICK}")
    time.sleep(1)
    send_bytes(f"JOIN {MAIN_CHANNEL}")
    return


def disconnect(ADMIN_NICK:str=cconf['admin_nick'], sslsock=sslsock) -> None:
    """Send a goodbye message to the admin and disconnects from the server."""
    send_message("Goodnight!", ADMIN_NICK)
    sslsock.shutdown(2)
    sslsock.close()
    return


def listen_for_msg(sslsock=sslsock):
    """Listen for messages from the IRC server."""
    raw_msg = sslsock.recv(4096).decode("UTF-8",errors='replace').strip("\r\n")
    return raw_msg


def reconnect_if_disconnected(raw_msg:str, sslsock=sslsock) -> None:
    """Reconnect to the server if the connection is lost."""
    if len(raw_msg) == 0:
        time.sleep(2)
        connect_to_server(sslsock)
    return


def rejoin_if_kicked(raw_msg:str, MAIN_CHANNEL:str=cconf['main_channel'],
                     BOT_NICK:int=cconf['bot_nick'], sslsock=sslsock) -> None:
    """Rejoin the channel if kicked."""
    if f"KICK {MAIN_CHANNEL} {BOT_NICK} :" in raw_msg:
        time.sleep(2)
        send_bytes(f"JOIN {MAIN_CHANNEL}")
        send_message("rude")
    return


def received_exit_code(target:str, nick:str, message:str,
                       BOT_NICK:int=cconf['bot_nick'],
                       ADMIN_NICK:str=cconf['admin_nick'],
                       sslsock=sslsock) -> bool:
    """Check if message is an exit code from the admin."""
    exit_condition = (
        target == BOT_NICK and
        nick == ADMIN_NICK and
        message == "goodnight"
    )
    return exit_condition


def message_is_valid(target:str, word_count:int, nick:str, command:str,
                     IGNORE_LIST:str=cconf['ignore_list'],
                     MAIN_CHANNEL:str=cconf['main_channel']) -> bool:
    """Check if message should be ignored or not."""
    valid_msg_condition = (
        nick != None and
        nick not in IGNORE_LIST and
        target == MAIN_CHANNEL and 
        command == 'PRIVMSG' and
        word_count > 0
    )
    if valid_msg_condition:
        return True




