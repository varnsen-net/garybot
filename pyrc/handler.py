import os
import re
import threading

# local modules
import pyrc.logger as logger
import pyrc.channel_functions.functions as fun # these functions are FUN! :^)
import pyrc.sportsbook.functions as sportsbook

# regular expressions
IMAGINE_REGEX = re.compile(r"^imagine unironically")
REASON_REGEX = re.compile(r"\breason\b")
DOTBE = "youtu\.be/([\w\d]{11})"
DOTCOM = "youtube\.com/watch\?v=([\w\d]{11})"
YOUTUBE_REGEX = re.compile(fr"{DOTBE}|{DOTCOM}")
TWITTER_REGEX = re.compile(r"twitter\.com/\w+/status/(\d+)")

# map triggers to functions
TRIGGER_MAP = {'.spaghetti': fun.dot_spaghetti,
               '.ask': fun.dot_ask,
               '.h': fun.dot_horoscope,
               '.wa': fun.dot_wolfram,
               '.apod': fun.dot_apod,
               '.sb': sportsbook.dot_sportsbook}


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

    # auto-replies
    if IMAGINE_REGEX.search(message):
        run(fun.imagine_without_iron, message, irc_client)

    if REASON_REGEX.search(message):
        run(fun.reason_will_prevail, irc_client)

    if (video_ids := YOUTUBE_REGEX.findall(message)):
        for video_id in video_ids:
            run(fun.fetch_youtube_stats, video_id, irc_client)

    if (tweet_ids := TWITTER_REGEX.findall(message)):
        for tweet_id in tweet_ids:
            run(fun.fetch_tweet, tweet_id, irc_client)

    # primary channel functions
    if trigger in TRIGGER_MAP.keys():
        run(TRIGGER_MAP[trigger], message_payload, irc_client)

    if trigger.startswith(irc_client.bot_nick):
        run(fun.dot_arb, message_payload, irc_client)

    return
