import random
import requests
import isodate
import urllib

import sqlite3
from google import genai
from google.genai import types
from pydantic import BaseModel

import src.channel_functions.helpers as helpers
import src.channel_functions.exceptions as exceptions
import src.config as config


class BotResponse(BaseModel):
    """"""
    user_nick: str
    user_message: str
    bot_reply_normal: str
    bot_reply_silly: str


def imagine_without_iron(message, irc_client):
    """
    Randomize the case of each letter of the user's message.
    
    :param str message: The user's message.
    :param object irc_client: The IRC client object (see: src/comms.py).
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
                        api_key=config.YOUTUBE_API_KEY):
    """
    Fetches stats for a youtube video from googleapis.
    
    :param str video_id: The youtube video id to fetch stats for.
    :param object irc_client: The IRC client object (see: src/comms.py).
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


def dot_spaghetti(message_payload, irc_client) -> None:
    """Return a random spaghetti quote."""
    selection = random.choice(config.SPAGHETTI_LYRICS)
    irc_client.send_message(selection, nick)
    return


def dot_ask(message_payload, irc_client):
    """
    Fetch a random line from a requested user's message history.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: src/comms.py).
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
                            correct_syntax=config.CORRECT_SYNTAX['.ask'])
        queried_nick = word_list[1]
        with sqlite3.connect("./user_logs.db") as db:
            results = db.execute(f"""
                SELECT message
                FROM user_logs
                WHERE nick = ?
                AND target = '{config.MAIN_CHANNEL}'
                AND message GLOB '[A-Za-z0-9]*'
                ORDER BY RANDOM()
                LIMIT 1;
            """, (queried_nick,))
            selection = results.fetchone()[0]
        response = f"<{queried_nick}> {selection}"
        irc_client.send_message(response)
    except exceptions.MissingArgsError as e:
        irc_client.send_message(e, nick)
    except FileNotFoundError:
        e = "I have no record of that user."
        irc_client.send_message(e, nick)
    return


def dot_wolfram(message_payload, irc_client):
    """
    Query Wolfram Alpha for a response.
    
    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: src/comms.py).
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    try:
        helpers.param_check(word_count,
                            required_params=1,
                            correct_syntax=config.CORRECT_SYNTAX['.wa'])
        api_key = f"&appid={config.WOLFRAM_API_KEY}"
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
    :param object irc_client: The IRC client object (see: src/comms.py).
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
    :param object irc_client: The IRC client object (see: src/comms.py).
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    with sqlite3.connect("./user_logs.db") as db:
        res = db.execute(
            f"""SELECT nick,message
            FROM user_logs
            WHERE target = '{config.MAIN_CHANNEL}'
            ORDER BY timestamp DESC
            LIMIT 500;"""
        ).fetchall()
    res.reverse()
    current_convo = "\n".join([f"<{r[0]}> {r[1]}"
                               for r in res])
    with open(config.PROJECT_WD / 'prompt', 'r') as f:
        sys_msg = f.read().format(current_convo=current_convo)
    client = genai.Client(api_key=config.LLM_KEY)
    response = client.models.generate_content(
        model=config.MODEL,
        config=types.GenerateContentConfig(
            system_instruction=sys_msg,
            response_mime_type='application/json',
            response_schema=list[BotResponse]),
        contents=f"<{nick}> {message}",
    )
    reply = (response.parsed[0].bot_reply_silly
             .strip('\n')
             .replace('\n\n', ' ')
             .replace('\n', ' '))
    irc_client.send_message(reply, nick)
    return

    

