import os
import re
import threading

# local modules
import pyrc.logger as logger
import pyrc.channel_functions.autoreplies as autoreplies
import pyrc.channel_functions.sundries as sundries
import pyrc.channel_functions.arbitrary as arb 
import pyrc.channel_functions.sportsbook as sportsbook

# regular expressions
IMAGINE_REGEX = re.compile(r"^imagine unironically")
REASON_REGEX = re.compile(r"\breason\b")
dotbe = "youtu\.be/([\w\d]{11})"
dotcom = "youtube\.com/watch\?v=([\w\d]{11})"
YOUTUBE_REGEX = re.compile(fr"{dotbe}|{dotcom}")
TWITTER_REGEX = re.compile(r"twitter\.com/\w+/status/(\d+)")

# map triggers to functions
TRIGGER_MAP = {'.spaghetti': sundries.dot_spaghetti,
               '.ask': sundries.dot_ask,
               '.h': sundries.dot_horoscope,
               '.wa': sundries.dot_wolfram,
               '.apod': sundries.dot_apod,
               '.sb': sportsbook.dot_sportsbook,
               }


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
        run(autoreplies.imagine_without_iron, message, irc_client)

    if REASON_REGEX.search(message):
        run(autoreplies.reason_will_prevail)

    if (video_ids := YOUTUBE_REGEX.findall(message)):
        run(autoreplies.fetch_youtube_stats, video_ids, irc_client)

    if (tweet_ids := TWITTER_REGEX.findall(message)):
        run(autoreplies.fetch_tweet, tweet_ids, irc_client)

    # primary channel functions
    if trigger in TRIGGER_MAP.keys():
        run(TRIGGER_MAP[trigger], message_payload, irc_client)

    if trigger.startswith(irc_client.bot_nick):
        run(arb.arb, message_payload, irc_client)

    return
