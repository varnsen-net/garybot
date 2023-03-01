import random
import requests
import isodate
import tweepy
import html
import urllib
import pandas as pd

# local imports
import pyrc.channel_functions.constants as constants
import pyrc.channel_functions.helpers as helpers
import pyrc.channel_functions.exceptions as exceptions


def imagine_without_iron(message, irc_client):
    """
    Randomize the case of each letter of the user's message.
    
    :param str message: The user's message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :returns: None
    :rtype: None
    """
    random_cased = "".join(random.choice([f.upper(),f]) for f in message)
    irc_client.send_message(random_cased)
    return


def reason_will_prevail(irc_client) -> None:
    """Duh."""
    irc_client.send_message('REASON WILL PREVAIL')
    return 


def fetch_youtube_stats(video_id,
                        irc_client,
                        api_key=constants.YOUTUBE_API_KEY):
    """
    Fetches stats for a youtube video from googleapis.
    
    :param str video_id: The youtube video id to fetch stats for.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :param str api_key: The youtube api key.
    :returns: A string containing stats on the youtube video.
    :rtype: str
    """
    path = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'id' : video_id,
        'key' : api_key,
        'part' : 'snippet,statistics,contentDetails'
    }
    response = requests.get(path, params).json()
    snippet = response['items'][0]['snippet']
    stats = response['items'][0]['statistics']
    content = response['items'][0]['contentDetails']

    # compose reply
    parts = {
        'Title' : snippet['title'],
        'Duration' : str(isodate.parse_duration(content['duration'])),
        'Uploader' : snippet['channelTitle'],
        'Uploaded' : snippet['publishedAt'][:10],
        'Views' : stats['viewCount'],
        'Likes' : stats['likeCount'],
    }
    parts_fmted = [f'26{e}: 04{parts[e]}' for e in parts.keys()]
    header = '01,00 You00,04Tube '
    response = ' | '.join([header] + parts_fmted)
    irc_client.send_message(response)
    return


def fetch_tweet(tweet_id,
                irc_client,
                twitter_key=constants.TWITTER_KEY,
                twitter_secret=constants.TWITTER_SECRET,
                twitter_access_token=constants.TWITTER_ACCESS_TOKEN,
                twitter_token_secret=constants.TWITTER_TOKEN_SECRET):
    """
    Fetches a tweet from the twitter api.
    
    :param str tweet_id: The id of the tweet to fetch.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :param str twitter_key: The twitter api key.
    :param str twitter_secret: The twitter api secret.
    :param str twitter_access_token: The twitter api access token.
    :param str twitter_token_secret: The twitter api token secret.
    :returns: None
    :rtype: None
    """
    auth = tweepy.OAuthHandler(twitter_key, twitter_secret)
    auth.set_access_token(twitter_access_token, twitter_token_secret)
    tpy = tweepy.API(auth)
    status = tpy.get_status(tweet_id, tweet_mode="extended")
    header = '00,02 Twitter '
    name = f"15{status.user.name}"
    text = status.full_text.replace('\n', ' ')
    text = f"02{text}"
    text = html.unescape(text)
    date = f"14{str(status.created_at)[:10]}"
    response = " | ".join([header, date, name, text])
    irc_client.send_message(response)
    return


def dot_spaghetti(message_payload, irc_client) -> None:
    """Return a random spaghetti quote."""
    selection = random.choice(constants.SPAGHETTI_LYRICS)
    irc_client.send_message(selection, nick)
    return


def dot_ask(message_payload, irc_client):
    """
    Fetch a random line from a requested user's message history.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
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
                            correct_syntax=constants.CORRECT_SYNTAX['.ask'])
        queried_nick = word_list[1]
        filepath = f"{constants.USER_LOGS_DIR}/{queried_nick}.csv"
        with open(filepath, "r", encoding="utf-8") as log:
            log = pd.read_csv(
                log, 
                index_col=False,
                usecols = [3],
                header = None,
            ).squeeze()
        sample_log = log.sample(69, replace=True).dropna()
        clean_log = sample_log[~sample_log.str.match('[,.!%]')]
        selection = str(clean_log.sample(1).iloc[0])
        response = f"<{queried_nick}> {selection}"
        irc_client.send_message(response)
    except exceptions.MissingArgsError as e:
        irc_client.send_message(e, nick)
    except FileNotFoundError:
        e = "I have no record of that user."
        irc_client.send_message(e, nick)
    return


def dot_horoscope(message_payload, irc_client):
    """
    Fetch a user's horoscope from the Horoscope API.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
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
                            correct_syntax=constants.CORRECT_SYNTAX['.h'])
        sign = word_list[1].lower()
        params = (
            ('sign', sign),
            ('day', 'today'),
        )
        resp = requests.post('https://aztro.sameerkumar.website/', params=params)
        horoscope = [f"{r.replace('_', ' ').title()}: {resp.json()[r]}"
                     for r in resp.json()]
        description = horoscope[2].split(' ', 1)[1]
        tidbits = ' | '.join(horoscope[3:8])
        header = constants.ZODIAC_SIGNS[sign]
        response = ' | '.join([header, description, tidbits])
        irc_client.send_message(response)
    except exceptions.MissingArgsError as e:
        irc_client.send_message(e, nick)
    except IndexError:
        e = 'That is not a valid astrological sign.'
        irc_client.send_message(e, nick)
    return


def dot_wolfram(message_payload, irc_client):
    """
    Query Wolfram Alpha for a response.
    
    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    try:
        helpers.param_check(word_count,
                            required_params=1,
                            correct_syntax=constants.CORRECT_SYNTAX['.wa'])
        api_key = f"&appid={constants.WOLFRAM_API_KEY}"
        url = "https://api.wolframalpha.com/v1/result?i="
        question = message.split(' ',1)[1]
        question = urllib.parse.quote_plus(question)
        apiquery = url + question + api_key + '&units=metric'
        
        # format and return the response
        response = requests.get(apiquery)
        response = response.text[:400].replace("\n", "")
        irc_client.send_message(response, nick)
    except exceptions.MissingArgsError as e:
        irc_client.send_message(e, nick)
    return
        

def dot_apod(message_payload, irc_client):
    """
    Fetch a random Astronomy Picture of the Day from NASA's API.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :return: None
    :rtype: None
    """
    apod_api = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=1"
    apod_data = requests.get(apod_api).json()[0]
    header = " AP🪐D "
    date = apod_data['date']
    title = apod_data['title']
    url = apod_data['hdurl']
    response = f"15,01{header} 14{date} 04{title}: 10{url}"
    irc_client.send_message(response)
    return


def dot_arb(message_payload, irc_client):
    """Responds to a message with a response from OpenAI's ChatGPT API.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: pyrc/comms.py).
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    bot_nick = irc_client.bot_nick
    if word_count == 1:
        query = "i've got nothing to say."
    else:
        query = message.split(' ', 1)[1]
    response = helpers.fetch_openai_response(nick, query, bot_nick)
    response = response['choices'][0]['message']['content']
    response = response.replace('\n', ' ').strip()
    irc_client.send_message(response, nick)
    return

    

