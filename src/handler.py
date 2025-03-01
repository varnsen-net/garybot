import os
import re
import threading

# local modules
import src.logger as logger
import src.channel_functions.functions as fun # these functions are FUN! :^)
import src.sportsbook.functions as sportsbook

# regular expressions
IMAGINE_REGEX = re.compile(r"^imagine unironically")
REASON_REGEX = re.compile(r"\breason\b")
DOTBE = "youtu\.be/([\w\d]{11})"
DOTCOM = "youtube\.com/watch\?v=([\w\d]{11})"
YOUTUBE_REGEX = re.compile(fr"{DOTBE}|{DOTCOM}")


def run(irc_function:callable, *args, **kwargs) -> None:
    """Run a channel or game function and log any errors that occur."""
    try:
        threading.Thread(target=irc_function, args=args, kwargs=kwargs).start()
    except:
        lock = threading.Lock()
        with lock:
            logger.log_error()
    return


def handler(message_payload, irc_client):
    """Determine which channel functions should be called.
    
    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None
    """
    trigger = message_payload['word_list'][0]
    message = message_payload['message']

    if IMAGINE_REGEX.search(message):
        run(fun.imagine_without_iron, message, irc_client)

    if REASON_REGEX.search(message):
        run(fun.reason_will_prevail, irc_client)

    if (video_ids := YOUTUBE_REGEX.findall(message)):
        for video_id in video_ids:
            run(fun.fetch_youtube_stats, video_id, irc_client)

    if message.startswith(irc_client.bot_nick):
        run(fun.dot_arb, message_payload, irc_client)

    match trigger:
        case '.spaghetti':
            run(fun.dot_spaghetti, message_payload, irc_client)
        case '.ask':
            run(fun.dot_ask, message_payload, irc_client)
        case '.wa':
            run(fun.dot_wolfram, message_payload, irc_client)
        case '.apod':
            run(fun.dot_apod, message_payload, irc_client)
        case '.sb':
            run(sportsbook.dot_sportsbook, message_payload, irc_client)

    return
