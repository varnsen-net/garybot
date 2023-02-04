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


