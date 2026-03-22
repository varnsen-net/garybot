import random
import requests
import isodate
import urllib

import sqlite3
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from gevent import sleep

import src.channel_functions.helpers as helpers
import src.channel_functions.exceptions as exceptions


CORRECT_SYNTAX = {'.ask': '.ask [nick]',
                  '.wa' : '.wa [query]'}

from pprint import pprint


class BotResponse(BaseModel):
    """"""
    user_nick: str = Field(description="The IRC nick of the user who sent the message.")
    user_message: str = Field(description="The message sent by the user.")
    bot_reply_intent: str = Field(description="The idea or intention behind the bot's reply.")
    bot_reply_normal: str = Field(description="The bot's reply in normal text.")
    bot_reply_reverse_text: str = Field(description="The bot's reply with the text reversed")


def imagine_without_iron(message):
    """
    Randomize the case of each letter of the user's message.
    
    :param str message: The user's message.
    :returns: None
    :rtype: None
    """
    return "".join(random.choice([f.upper(),f]) for f in message)


def reason_will_prevail():
    """Duh."""
    return 'REASON WILL PREVAIL'


def dot_spaghetti():
    """Return a random spaghetti quote."""
    SPAGHETTI_LYRICS = (
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
        "Make me spaghetti as we move toward a new world order.")
    return random.choice(SPAGHETTI_LYRICS)


def dot_ask(user_logs_path, target, word_count, word_list):
    """
    Fetch a random line from a requested user's message history.

    :raises MissingArgsError: If the user did not provide a nick to query.
    :raises: FileNotFoundError: If the user's message history cannot be found.
    """
    try:
        helpers.param_check(word_count,
                            required_params=1,
                            correct_syntax=CORRECT_SYNTAX['.ask'])
        queried_nick = word_list[1]
        with sqlite3.connect(user_logs_path) as db:
            results = db.execute("""
                SELECT message
                FROM user_logs
                WHERE nick = ?
                AND target = ?
                AND message GLOB '[A-Za-z0-9]*'
                ORDER BY RANDOM()
                LIMIT 1;
            """, (queried_nick, target))
            selection = results.fetchone()[0]
        return f"<{queried_nick}> {selection}"
    except exceptions.MissingArgsError as e:
        return e
    except TypeError:
        return f"Sorry, I have no record of {queried_nick} in {target}."


def dot_wolfram(message_payload, irc_client, app_config):
    """
    Query Wolfram Alpha for a response.
    
    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    word_count = message_payload['word_count']
    correct_syntax = CORRECT_SYNTAX['.wa']
    wolfram_api_key = app_config.wolfram_api_key
    try:
        helpers.param_check(word_count,
                            required_params=1,
                            correct_syntax=correct_syntax)
        api_key = f"&appid={wolfram_api_key}"
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


def dot_arb(nick, target, message, llm_api_key, llm_model, user_logs_path,
            main_channel, project_root, client_nick):
    """Responds to a message with a response from OpenAI's ChatGPT API.

    :return: None
    :rtype: None
    """
    with sqlite3.connect(user_logs_path) as db:
        res = db.execute(
            """SELECT nick,message
            FROM user_logs
            WHERE target = ?
            ORDER BY timestamp DESC
            LIMIT 100;"""
            , (main_channel,)
        ).fetchall()
    res.reverse()
    current_convo = "\n".join([f"<{r[0]}> {r[1]}"
                               for r in res])
    with open(project_root / 'prompt', 'r') as f:
        sys_msg = f.read().format(current_convo=current_convo, client_nick=client_nick)
    client = genai.Client(api_key=llm_api_key)
    response = client.models.generate_content(
        model=llm_model,
        config=types.GenerateContentConfig(
            system_instruction=sys_msg,
            response_mime_type='application/json',
            response_schema=list[BotResponse],
            max_output_tokens=500,
        ),
        contents=f"<{nick}> {message}",
    )
    pprint(response)
    reply = (response.parsed[0].bot_reply_reverse_text[::-1]
             .strip('\n')
             .replace('\n\n', ' ')
             .replace('\n', ' '))
    return f"{nick}: {reply}"

    

