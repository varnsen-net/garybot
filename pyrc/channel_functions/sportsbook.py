import os
from datetime import datetime as dt
from dateutil import tz
from time import time
import requests
import json

# local modules
import pyrc.comms as comms
import pyrc.channel_functions.exceptions as exceptions

_SPORT_KEY_MAP = {
    'nfl' : 'americanfootball_nfl',
    'cfb' : 'americanfootball_ncaaf',
    'mlb' : 'baseball_mlb',
    'nhl' : 'icehockey_nhl',
    'nba' : 'basketball_nba',
}
_ODDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'odds')
_ODDS_API_KEY = os.getenv('ODDS_API_KEY')


def fetch_league_odds_from_api(sport_key, bookmaker='unibet', odds_api_key=_ODDS_API_KEY):
    """
    Fetches NFL moneyline odds from the Odds API for the given bookmaker.
    
    Parameters
    ----------
    sport_key : str
        The sport to fetch odds for. Valid strings are given in the
        sport_key_map dictionary values.
    odds_api_key : str
        API key for the Odds API — https://the-odds-api.com/
    bookmaker : str
        Bookmaker to fetch odds from. Default is 'bovada'.
        
    Returns
    -------
    response : Response
        Response object from the Odds API.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    markets = 'h2h,spreads'
    odds_format = 'american'
    date_format = 'iso'
    response = requests.get(
        url = url,
        params = {
            'api_key' : odds_api_key,
            'markets' : markets,
            'oddsFormat' : odds_format,
            'dateFormat' : date_format,
            'bookmakers' : bookmaker,
        }
    )
    return response


def check_for_valid_query(word_list):
    """
    Checks if the user provided a team and valid league to query.
    
    Parameters
    ----------
    word_list : list
        Every word in the user's message.

    Returns
    -------
    None
    
    Raises
    ------
    InvalidQuery
        If the user did not provide a team and valid league to query.
    """
    if len(word_list) < 3:
        raise exceptions.InvalidQuery(_SPORT_KEY_MAP)
    league = word_list[1].lower()
    if league not in _SPORT_KEY_MAP.keys():
        raise exceptions.InvalidQuery(_SPORT_KEY_MAP)
    return


def write_new_league_odds_file(sport_key, filepath):
    """
    Writes a new league odds file to the book-odds directory.

    :param str sport_key: The sport to fetch odds for. Valid strings are given in the sport_key_map dictionary values.
    :param str filepath: The path to the file to write.
    :return: None
    :rtype: None
    """
    response = fetch_league_odds_from_api(sport_key)
    if response.status_code != 200:
        raise exceptions.BadStatusCode(response.status_code)
    else:
        #TODO: check if dir exists first
        with open(filepath, 'w') as file:
            json.dump(response.json(), file)
        print('Remaining requests', response.headers['x-requests-remaining'])
        print('Used requests', response.headers['x-requests-used'])
    return


def league_odds_file_is_old(filepath, minutes=10):
    """
    Checks if the league odds file is older than the given number of minutes.

    :param str filepath: The path to the file to check.
    :param int minutes: The number of minutes to check.
    :return: True if the file is older than the given number of minutes, False otherwise.
    :rtype: bool
    """
    with open(filepath, 'r') as file: 
        last_modified = os.stat(filepath).st_mtime
    current_time = time()
    delta = current_time - last_modified
    delta_frac = delta / 60 / minutes
    return True if delta_frac > 1.0 else False


def update_odds_file_if_necessary(league):
    """
    Checks if the league odds file is older than the given number of minutes. If so, fetches new odds from the Odds API.

    :param str league: The league to check.
    :return: None
    :rtype: None
    """
    sport_key = _SPORT_KEY_MAP[league]
    filepath = f"{_ODDS_DIR}/{sport_key}.json"
    if not os.path.exists(filepath) or league_odds_file_is_old(filepath):
        write_new_league_odds_file(sport_key, filepath)
    return


def load_league_odds(league):
    """
    Loads the league odds from the league odds file.

    :param str league: The league to load.
    :return: The league odds.
    :rtype: dict
    """
    sport_key = _SPORT_KEY_MAP[league]
    filepath = f"{_ODDS_DIR}/{sport_key}.json"
    with open(filepath, 'r') as file: 
        league_odds = json.load(file)
    return league_odds


def search_for_game_odds(word_list, league_odds):
    """
    Searches the league odds for the game the user is looking for.

    :param list word_list: Every word in the user's message.
    :param dict league_odds: The league odds to search.
    :return: The game odds.
    :rtype: dict
    """
    # inform user if no odds are found
    if len(league_odds) == 0:
        raise exceptions.NoOddsFound()
    
    # search for game odds
    user_query = ' '.join(word_list[2:]).lower()
    game_odds = [
        g 
        for g in league_odds 
        if user_query in g['home_team'].lower()
        or user_query in g['away_team'].lower()
    ]
    
    # inform user if no game was found
    if len(game_odds) == 0:
        raise exceptions.NoGameFound()
    
    return game_odds[0]


def extract_game_info(game_odds):
    """
    Extracts single game moneyline and spread from the game odds dict.

    :param dict game_odds: The game odds to extract.
    :return: The game info.
    :rtype: tuple
    """
    tipoff = format_timestamp(game_odds['commence_time'])
    home_team = game_odds['home_team']
    away_team = game_odds['away_team']
    
    # fetch market data
    try:
        markets = game_odds['bookmakers'][0]
    except IndexError:
        raise exceptions.NoGameOddsFound()

    # fetch moneyline data
    try:
        h2h_outcomes = markets['markets'][0]['outcomes']
        away_h2h = [f['price'] for f in h2h_outcomes if f['name'] == away_team][0]
        home_h2h = [f['price'] for f in h2h_outcomes if f['name'] == home_team][0]
        h2h = [away_h2h, home_h2h]
    except IndexError:
        h2h = ['None', 'None']
    
    # fetch spread data
    try:
        spread_outcomes = markets['markets'][1]['outcomes']
        away_spread = [f['point'] for f in spread_outcomes if f['name'] == away_team][0]
        home_spread = [f['point'] for f in spread_outcomes if f['name'] == home_team][0]
        spreads = [away_spread, home_spread]
    except IndexError:
        spreads = ['None', 'None']

    return (tipoff, away_team, h2h[0], spreads[0], home_team, h2h[1], spreads[1])


def format_timestamp(timestamp:str) -> str:
    """Formats a timestamp from the Odds API to CST."""
    tipoff = dt.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    central_tz = tz.gettz('America/Chicago')
    tipoff_cst = tipoff.astimezone(central_tz)
    tipoff_cst = dt.strftime(tipoff_cst, '%a %b %d, %I:%M%p CST')
    return tipoff_cst


def abbreviate_team_name(team_name:str) -> str:
    """
    Assume that if the team name has more than two words in it, the first two words belong to the city name.
    """
    words = team_name.split(' ')
    if len(words) > 2:
        initials = [l[0] for l in words[:2]]
        team_name_abbrv = ''.join(initials)
    else:
        team_name_abbrv = words[0][:3].upper()
    return team_name_abbrv


def format_reply(game_info:tuple) -> str:
    """Formats the game info into a reply string."""
    away_abbrv = abbreviate_team_name(game_info[1])
    home_abbrv = abbreviate_team_name(game_info[4])
    matchup = f"{game_info[1]} @ {game_info[4]}"
    moneyline = f"07Moneyline: {away_abbrv} {game_info[2]} {home_abbrv} {game_info[5]}"
    spread = f"09Spread: {away_abbrv} {game_info[3]} {home_abbrv} {game_info[6]}"
    tipoff = game_info[0]
    tipoff_cst = f"14{tipoff}"
    reply = ' | '.join([matchup, moneyline, spread, tipoff_cst])
    return reply


def dot_sportsbook(message_payload):
    nick = message_payload['nick']
    word_list = message_payload['word_list']
    try:
        check_for_valid_query(word_list)
        league = word_list[1]
        update_odds_file_if_necessary(league)
        league_odds = load_league_odds(league)
        game_odds = search_for_game_odds(word_list, league_odds)
        game_info = extract_game_info(game_odds)
        reply = format_reply(game_info)
        comms.send_message(reply)
    except exceptions.InvalidQuery as e:
        comms.send_message(e, nick)
    except exceptions.BadStatusCode as e:
        comms.send_message(e, nick)
    except exceptions.NoOddsFound as e:
        comms.send_message(e, nick)
    except exceptions.NoGameFound as e:
        comms.send_message(e, nick)
    except exceptions.NoGameOddsFound as e:
        comms.send_message(e, nick)

