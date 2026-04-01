import random
import requests
import urllib
from html import unescape

import sqlite3
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class BotResponse(BaseModel):
    """Structured schema for the IRC bot's reply to a user message.
 
    Captures the original message context alongside the bot's response
    in multiple formats, including a reversed-text variant used for output.
 
    Attributes:
        user_nick: IRC nick of the user who sent the message.
        user_message: The raw message sent by the user.
        bot_reply_intent: The intended meaning or goal of the bot's reply,
            used as an intermediate reasoning step.
        bot_reply_normal: The bot's reply written in plain text.
        bot_reply_reverse_text: The bot's reply with characters in reverse
            order, which is reversed back to normal before sending.
    """
    user_nick: str = Field(description="The IRC nick of the user who sent the message.")
    user_message: str = Field(description="The message sent by the user.")
    bot_reply_intent: str = Field(description="The idea or intention behind the bot's reply.")
    bot_reply_normal: str = Field(description="The bot's reply in normal text.")
    bot_reply_reverse_text: str = Field(description="The bot's reply with the text reversed")


def imagine_without_iron(message):
    """Return the message with each character's case randomized.
 
    :param str message: The input string to randomize.
    :returns: The message with randomly mixed casing.
    :rtype: str
    """
    return "".join(random.choice([f.upper(),f]) for f in message)


def reason_will_prevail():
    """Duh."""
    return 'REASON WILL PREVAIL'


def dot_spaghetti():
    """Return a random Eminem lyric with 'spaghetti' substituted in.
 
    :returns: A randomly selected spaghetti lyric.
    :rtype: str
    """
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


def dot_ask(queried_nick, target, user_logs_path):
    """Fetch a random message from a user's log history in a given channel.
 
    :param str queried_nick: The IRC nick to retrieve a random quote from.
    :param str target: The channel name to scope the query to.
    :param pathlib.Path user_logs_path: Filesystem path to the SQLite user
        log database.
    :returns: A formatted quote string ``<nick> message``.
    :rtype: str
    """
    try:
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
    except TypeError:
        return f"Sorry, I have no record of {queried_nick} in {target}."


def dot_wolfram(nick, message, wolfram_api_key):
    """Query the Wolfram Alpha short-answer API and return the result.
 
    :param str nick: The IRC nick of the requesting user, prepended to the
        reply.
    :param str message: The full command string; everything after the first
        whitespace-delimited token is treated as the query.
    :param str wolfram_api_key: A valid Wolfram Alpha API application key.
    :returns: A string in the form ``nick: <wolfram response>``.
    :rtype: str
    """
    api_key = f"&appid={wolfram_api_key}"
    url = "https://api.wolframalpha.com/v1/result?i="
    question = message.split(' ',1)[1]
    question = urllib.parse.quote_plus(question)
    apiquery = url + question + api_key + '&units=metric'
    
    # format and return the response
    response = requests.get(apiquery)
    if response.status_code != 200:
        return f"{nick}: Sorry, I couldn't get an answer to that question."
    response = response.text[:400].replace("\n", "")
    return f"{nick}: {response}"
        

def dot_apod(nick, nasa_api_key):
    """Fetch a random NASA Astronomy Picture of the Day and format it for IRC.
 
    :param str nick: The IRC nick of the requesting user, prepended to the
        reply.
    :param str nasa_api_key: A valid NASA API key.
    :returns: A string in the form ``nick: <IRC-formatted APOD line>``.
    :rtype: str
    """
    apod_api = f"https://api.nasa.gov/planetary/apod?api_key={nasa_api_key}&count=1"
    apod_data = requests.get(apod_api).json()[0]
    header = " AP🪐D "
    date = apod_data['date']
    title = apod_data['title']
    url = f"https://apod.nasa.gov/apod/ap{date[2:].replace('-','')}.html"
    response = f"15,01{header} 14{date} 04{title}: 10{url}"
    return f"{nick}: {response}"


def dot_arb(nick, message, llm_api_key, llm_model, current_convo,
            project_root, client_nick):
    """Generate a contextual reply using the Google Gemini API.
 
    If the model does not finish cleanly (finish reason other than
    `"STOP"`), a fallback error string is returned instead.
 
    :param str nick: IRC nick of the user sending the message.
    :param str message: The user's message text.
    :param str llm_api_key: Google Gemini API key.
    :param str llm_model: Gemini model identifier (e.g. ``"gemini-2.0-flash"``).
    :param str current_convo: Recent channel conversation, injected into the
        system prompt for context.
    :param pathlib.Path project_root: Root directory of the project, used to
        locate the prompt file.
    :param str client_nick: The bot's own IRC nick, injected into the system
        prompt.
    :returns: A string in the form ``nick: <reply>``, or an error message if
        the model did not return a complete response.
    :rtype: str
    """
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
    finish_reason = response.candidates[0].finish_reason.name
    if finish_reason == "STOP":
        reply = (response.parsed[0].bot_reply_reverse_text[::-1]
                 .strip('\n')
                 .replace('\n\n', ' ')
                 .replace('\n', ' '))
    else:
        reply = f"Sorry, I couldn't generate a complete response: {finish_reason}"
    return f"{nick}: {reply}"

    
def dot_trivia(nick):
    """"""
    trivia_api = "https://opentdb.com/api.php?amount=1&difficulty=medium&type=multiple"
    response = requests.get(trivia_api).json()
    if response['response_code'] != 0:
        return f"{nick}: Sorry, I couldn't fetch a trivia question right now."
    question_data = response['results'][0]
    category = question_data['category']
    question = unescape(question_data['question'])
    correct_answer = unescape(question_data['correct_answer'])
    incorrect_answers = [unescape(ans) for ans in question_data['incorrect_answers']]
    options = incorrect_answers + [correct_answer]
    random.shuffle(options)
    options_str = ' '.join(f"({l}) {opt}" for l, opt in zip('abcd', options))
    return f"{nick}: 15,01TRIVIA 🧐 04{category}: {question} {options_str}"
