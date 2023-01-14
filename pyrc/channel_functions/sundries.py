import os
import random
import pandas as pd
import requests
import urllib

# local modules
import pyrc.comms as comms
import pyrc.channel_functions.helpers as helpers
import pyrc.channel_functions.exceptions as exceptions

# global variables
_USER_LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'user-logs')
_WOLFRAM_API_KEY = os.environ.get('WOLFRAM_API_KEY')
_SPAGHETTI_LYRICS = (
    "Lose yourself in Mom's spaghetti. It's ready.",
    "You only get one spaghetti.",
    "Spaghetti only comes once in a lifetime.",
    "Amplified by the fact that I keep on forgetting to make spaghetti.",
    "Tear this motherfucking roof off like two Mom's spaghettis.",
    "Look, if you had Mom's spaghetti, would you capture it, or just let it slip?",
    "There's vomit on his sweater spaghetti, Mom's spaghetti.",
    "He opens his mouth but spaghetti won't come out.",
    "Snap back to spaghetti.",
    "Oh, there goes spaghetti.",
    "He knows he keeps on forgetting Mom's spaghetti.",
    "Mom's spaghetti's mine for the taking.",
    "He goes home and barely knows his own Mom's spaghetti.",
    "Mom's spaghetti's close to post mortem.",
    "No more games. I'ma change what you call spaghetti.",
    "Man these goddamn food stamps don't buy spaghetti.",
    "This may be the only Mom's spaghetti I got.",
    "Make me spaghetti as we move toward a new world order."
    )
_CORRECT_SYNTAX = {'.ask': '.ask [nick]',
                   '.h'  : '.h [sign]',
                   '.wa' : '.wa [query]'}


def dot_spaghetti(message_payload) -> None:
    """Return a random spaghetti quote."""
    selection = random.choice(_SPAGHETTI_LYRICS)
    comms.send_message(selection, message_payload['nick'])
    return


def dot_ask(message_payload):
    """Fetch a random line from a requested user's message history.

    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None

    :raises MissingArgsError: If the user did not provide a nick to query.
    :raises: FileNotFoundError: If the user's message history cannot be found.
    """
    word_count = message_payload['word_count']
    word_list = message_payload['word_list']
    nick = message_payload['nick']
    try:
        helpers.param_check(word_count,
                    required_params=1,
                    correct_syntax=_CORRECT_SYNTAX['.ask'])
        queried_nick = word_list[1]
        filepath = f"{_USER_LOGS_DIR}/{queried_nick}.csv"
        with open(filepath, "r", encoding="utf-8") as log:
            log = pd.read_csv(
                log, 
                index_col=False,
                usecols = [3],
                # squeeze = True, #TODO squeeze has been deprecated
                header = None,
            ).squeeze()
        sample_log = log.sample(69, replace=True).dropna()
        clean_log = sample_log[~sample_log.str.match('[,.!%]')]
        selection = str(clean_log.sample(1).iloc[0])
        response = f"<{queried_nick}> {selection}"
        comms.send_message(response, nick)
    except exceptions.MissingArgsError as e:
        comms.send_message(e, nick)
    except FileNotFoundError:
        e = "I have no record of that user."
        comms.send_message(e, nick)
    return


def dot_horoscope(message_payload):
    """Fetch a user's horoscope from the Horoscope API.

    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None

    :raises MissingArgsError: If the user did not provide a sign to query.
    :raises IndexError: If the user provided an invalid sign.
    """
    word_count = message_payload['word_count']
    word_list = message_payload['word_list']
    nick = message_payload['nick']
    try:
        helpers.param_check(word_count,
                    required_params=1,
                    correct_syntax=_CORRECT_SYNTAX['.h'])
        sign = word_list[1]
        params = (
            ('sign', sign.lower()),
            ('day', 'today'),
        )
        resp = requests.post('https://aztro.sameerkumar.website/', params=params)
        horoscope = [f.replace('_', ' ').title() + ": " + resp.json()[f] for f in resp.json()]
        description = horoscope[2].split(' ', 1)[1]
        tidbits = ' | '.join(horoscope[3:8])
        response = ' | '.join([description, tidbits])
        comms.send_message(response, nick)
    except exceptions.MissingArgsError as e:
        comms.send_message(e, nick)
    except IndexError:
        e = 'That is not a valid astrological sign.'
        comms.send_message(e, nick)
    return


def dot_wolfram(message_payload):
    """Query Wolfram Alpha for a response.
    
    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    try:
        helpers.param_check(word_count,
                    required_params=1,
                    correct_syntax=_CORRECT_SYNTAX['.wa'])
        api_key = f"&appid={_WOLFRAM_API_KEY}"
        url = "https://api.wolframalpha.com/v1/result?i="
        question = message.split(' ',1)[1]
        question = urllib.parse.quote_plus(question)
        apiquery = url + question + api_key + '&units=metric'
        
        # format and return the response
        response = requests.get(apiquery)
        response = response.text[:400].replace("\n", "")
        comms.send_message(response, nick)
    except exceptions.MissingArgsError as e:
        comms.send_message(e, nick)
    return
        

def dot_apod(message_payload):
    """Fetch a random Astronomy Picture of the Day from NASA's API."""
    nick = message_payload['nick']
    apod_api = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=1"
    apod_data = requests.get(apod_api).json()[0]
    date = apod_data['date']
    title = apod_data['title']
    url = apod_data['hdurl']
    response = f"14{date} 04{title}: 10{url}"
    comms.send_message(response, nick)



