import os
import openai
import dotenv


# local modules
import pyrc.comms as comms

_OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def fetch_openai_response(nick, query, bot_nick):
    """
    Fetches a response from OpenAI's ChatGPT API.

    Because I am a better programmer than pardisfla, my bot's prompt can be
    updated on the fly.

    :param str nick: The nick of the user who sent the message.
    :param str query: The message sent by the user.
    :param str botnick: The nick of the bot.
    :return: The response from OpenAI.
    :rtype: openai.Completion
    """
    CHATGPT_PROMPT = dotenv.dotenv_values('./prompt')['CHATGPT_PROMPT']
    prompt = CHATGPT_PROMPT.format(nick=nick, query=query, bot_nick=bot_nick)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.9,
        max_tokens=69, # lmao
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response


def arb(message_payload, bot_nick):
    """Responds to a message with a response from OpenAI's ChatGPT API.

    :param dict message_payload: The message payload parsed from the raw message.
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    message = message_payload['message']
    if message_payload['word_count'] == 1:
        query = "i've got nothing to say."
    else:
        query = message.split(' ', 1)[1]
    response = fetch_openai_response(nick, query, bot_nick)
    response = response.choices[0].text
    response = response.replace('\n', ' ').strip()
    comms.send_message(response, nick)
    return

    
# old pipeline
# ------------
# from transformers import pipeline, Conversation
# from random import randint

# generator = pipeline('conversational', model='microsoft/DialoGPT-medium', framework='pt', device=-1)


# def ArbReply(msg_obj, pyrc_obj):
    # try:
        # user_msg = msg_obj.message.split(' ', 1)[1]
    # except IndexError:
        # user_msg = 'my balls are bigger than my balls.'
    # min_len = randint(1,50)
    # convo = Conversation(user_msg)
    # reply = generator(
        # convo, 
        # do_sample = True,
        # min_length = min_len, 
        # num_return_sequences = 1,
    # )
    # reply_text = str(reply).split('>> ')[-1]
    # reply_text = msg_obj.nick + ': ' + reply_text 
    # return reply_text, pyrc_obj.channel

