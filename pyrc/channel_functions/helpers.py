import openai
import dotenv
import pyrc.channel_functions.exceptions as exceptions


def param_check(word_count, required_params, correct_syntax):
    """
    Sanity-check the number of parameters in a user's message.

    :param list[str] word_list: Each word in the user's message.
    :param int required_params: The number of parameters required. 
    :param str correct_syntax: Describes the correct synatx for the function
        the user called.
    :return: None
    :rtype: None

    :raises MissingArgsError: If the user's message does not contain enough
        parameters.
    """
    if word_count - 1 < required_params: # -1 to account for the command itself
        raise exceptions.MissingArgsError(correct_syntax)
    return


def fetch_openai_response(nick, query, bot_nick):
    """
    Fetches a response from OpenAI's ChatGPT API.

    :param str nick: The nick of the user who sent the message.
    :param str query: The message sent by the user.
    :param str bot_nick: The nick of the bot.
    :return: The response from OpenAI.
    :rtype: openai.Completion
    """
    CHATGPT_PROMPT = dotenv.dotenv_values('./prompt')['CHATGPT_PROMPT']
    prompt = CHATGPT_PROMPT.format(nick=nick, bot_nick=bot_nick)
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": query},],
        temperature=0.8,
        max_tokens=69, # lmao
        frequency_penalty=0,
        presence_penalty=0
    )
    return response


