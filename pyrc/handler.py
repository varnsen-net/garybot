import re
import threading
import pyrc.logger as logger
import pyrc.channel_functions.autoreplies as autor 


def thread(func):
    """Decorator. Thread a function."""
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()
        return
    return wrapper


@thread
def run(irc_function, *args, **kwargs):
    """Run a channel or game function and log any errors that occur."""
    try:
        irc_function(*args, **kwargs)
    except:
        lock = threading.Lock()
        with lock:
            logger.log_error()
    return


def handler(nick:str, message:str, word_list:list[str]):
    """Determine which channel functions should be called."""
    trigger = word_list[0]

    # TODO compile regexes at top of module
    if re.search(r"^imagine unironically", message) is not None:
        run(autor.imagine_without_iron, message)

    if re.search(r"\breason\b", message) is not None:
        run(autor.reason_will_prevail)

    if len((video_ids := autor.find_youtube_ids(message))) > 0:
        run(autor.send_youtube_stats, video_ids)

    if len((tweet_ids := autor.find_tweet_ids(message))) > 0:
        run(autor.send_tweet_stats, tweet_ids)
