# local modules
import src.sportsbook.helpers as helpers
import src.sportsbook.exceptions as exceptions


def dot_sportsbook(message_payload, irc_client):
    """
    Fetches the sportsbook odds for a given league and team.

    :param dict message_payload: The message payload parsed from the raw message.
    :param object irc_client: The IRC client object (see: src/comms.py).
    :return: None
    :rtype: None
    """
    nick = message_payload['nick']
    word_list = message_payload['word_list']
    try:
        helpers.check_for_valid_query(word_list)
        league = word_list[1]
        helpers.update_odds_file_if_necessary(league)
        league_odds = helpers.load_league_odds(league)
        game_odds = helpers.search_for_game_odds(word_list, league_odds)
        game_info = helpers.extract_game_info(game_odds)
        reply = helpers.format_reply(game_info)
        irc_client.send_message(reply)
    except exceptions.InvalidQuery as e:
        irc_client.send_message(e, nick)
    except exceptions.BadStatusCode as e:
        irc_client.send_message(e, nick)
    except exceptions.NoOddsFound as e:
        irc_client.send_message(e, nick)
    except exceptions.NoGameFound as e:
        irc_client.send_message(e, nick)
    except exceptions.NoGameOddsFound as e:
        irc_client.send_message(e, nick)
    return

