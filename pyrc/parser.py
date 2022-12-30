import re


def parse_raw_msg(raw_msg:str, prefix:str=None, command:str=None,
                  target:str=None, message:str=None) -> list[str]:
    """Use a regex to split the raw IRC string into its prefix, command,
    target, and message."""
    regex = r":(\S+\!\S+@\S+) ([A-Z]+) (\S+) :(.+)"
    p = re.compile(regex)
    matches = p.match(raw_msg)
    if matches:
        prefix = matches.group(1) # group 0 is the full match
        command = matches.group(2)
        target = matches.group(3)
        message = matches.group(4)
    return prefix, command, target, message
        

def parse_prefix(prefix:str, nick:str=None, ident:str=None) -> list[str]:
    """Split the prefix into the user's nick and ident."""
    if prefix:
        nick, ident = prefix.split('!', 1)
        ident = ident.split('@', 1)[0]
    return nick, ident


def get_word_count(message:str, word_count:int=None) -> int:
    """Count the words in the message."""
    if message:
        word_list = message.split(' ')
        word_list = list(filter(None, word_list))
        word_count = len(word_list)
    return word_count


def get_word_list(message:str, word_list:list[str]=None) -> list[str]:
    """Transform the message into a list of words."""
    if message:
        word_list = message.split(' ')
    return word_list


def parse(raw_msg:str) -> list[str]:
    """Use the parsing functions to parse the raw string into its components."""
    prefix, command, target, message = parse_raw_msg(raw_msg)
    nick, ident = parse_prefix(prefix)
    word_count = get_word_count(message)
    word_list = get_word_list(message)
    return ident, nick, target, message, command, word_count, word_list 


