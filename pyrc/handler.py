import re
import threading


# local modules
import pyrc.logger as logger
import pyrc.channel_functions.autoreplies as autor 


# regular expressions
IMAGINE_REGEX = re.compile(r"^imagine unironically")
REASON_REGEX = re.compile(r"\breason\b")
dotbe = "youtu\.be/([\w\d]{11})"
dotcom = "youtube\.com/watch\?v=([\w\d]{11})"
YOUTUBE_REGEX = re.compile(fr"{dotbe}|{dotcom}")
TWITTER_REGEX = re.compile(r"twitter\.com/\w+/status/(\d+)")


def thread(func:callable) -> callable:
    """Decorator to thread a function."""
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()
        return
    return wrapper


@thread
def run(irc_function:callable, *args, **kwargs) -> None:
    """Run a channel or game function and log any errors that occur."""
    try:
        irc_function(*args, **kwargs)
    except:
        lock = threading.Lock()
        with lock:
            logger.log_error()
    return


def handler(nick, message, word_list):
    """Determine which channel functions should be called.
    
    :param str nick: The nick of the user who sent the message.
    :param str message: The message sent by the user.
    :param list[str] word_list: The message split into a list of words.
    :return: None
    :rtype: None
    """
    trigger = word_list[0]

    # TODO compile regexes at top of module
    if IMAGINE_REGEX.search(message) is not None:
        run(autor.imagine_without_iron, message)

    if REASON_REGEX.search(message) is not None:
        run(autor.reason_will_prevail)

    if len((video_ids := YOUTUBE_REGEX.findall(message))) > 0:
        run(autor.fetch_youtube_stats, video_ids)

    if len((tweet_ids := TWITTER_REGEX.findall(message))) > 0:
        run(autor.fetch_tweet, tweet_ids)

    return
