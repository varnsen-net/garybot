from os import getcwd
import configparser
import openai

config_path = getcwd() + '/config.ini'
config = configparser.ConfigParser()
config.read(config_path)
botnick = config['connection']['botnick']
openai.api_key = config['api_keys']['openai_api_key']

def FetchOpenAIResponse(botnick, nick, user_msg):
    prompt = f"this is a conversation with a hyper-intelligent machine mind called Arbitrary. it has strong opinions on EVERYTHING. it very occasionally uses emojis.\n\n{nick}: {user_msg}\nArbitrary:"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.9,
        max_tokens=69,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response

def ArbReply(msg_obj, pyrc_obj):
    try:
        user_msg = msg_obj.message.split(' ', 1)[1]
    except IndexError:
        user_msg = "i've got nothing to say."
    response = FetchOpenAIResponse(pyrc_obj.botnick, msg_obj.nick, user_msg)
    response = response.choices[0].text
    response = response.replace('\n', ' ').strip()
    reply_text = f"{msg_obj.nick}: {response}"
    return reply_text, pyrc_obj.channel

if __name__ == "__main__":
    class testobj:
        def __init__(self):
            self.message = "buttebot: who are you?"
            self.nick = 'gary'
            self.channel = '#channel'
            self.botnick = 'buttebot'

    to = testobj()
    reply = ArbReply(to, to)
    print(reply[0])
    
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

