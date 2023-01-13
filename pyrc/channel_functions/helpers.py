import pyrc.channel_functions.exceptions as exceptions


def param_check(word_count, required_params, correct_syntax):
    """Sanity check for the ask_user function.

    :param list[str] word_list: Each word in the user's message.
    :param int required_params: The number of parameters required for the function.
    :param str correct_syntax: Describes the correct synatx for the function.
    :return: None
    :rtype: None
    """
    if word_count - 1 < required_params: # -1 to account for the command itself
        raise exceptions.MissingArgsError(correct_syntax)
    return


