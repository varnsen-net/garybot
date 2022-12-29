from os import getcwd, stat, path
from datetime import datetime as dt
from dateutil import tz
from time import time
import requests
import configparser
import json


# TODO: handle exceptions for missing key
config_path = getcwd() + '/config.ini'
config = configparser.ConfigParser()
config.read(config_path)
odds_api_key = config['api_keys']['odds_api_key']

# available leagues
sport_key_map = {
    'nfl' : 'americanfootball_nfl',
    'cfb' : 'americanfootball_ncaaf',
    'mlb' : 'baseball_mlb',
    'nhl' : 'icehockey_nhl',
    'nba' : 'basketball_nba',
}

# exceptions
class InvalidQuery(Exception):
    """User failed to provide anything to query"""
    def __init__(self, nick, key_map):
        self.leagues = ', '.join(key_map.keys())
        self.errmsg = f"{nick}: To use the sportsbook function, try: .sb [league] [city or team name]. Valid leagues are {self.leagues}."

class BadStatusCode(Exception):
    """Failed to pull data from Odds API"""
    def __init__(self, nick, code):
        self.errmsg = f"{nick}: Failed to fetch odds: status code {code}."

class NoOddsFound(Exception):
    """Could not find any odds in the response JSON"""
    def __init__(self, nick):
        self.errmsg = f"{nick}: The API returned no data. Try again later."

class NoGameFound(Exception):
    """Could not find odds for the queried team"""
    def __init__(self, nick):
        self.errmsg = f"{nick}: The API has no matchup for that city or team name."

class NoGameOddsFound(Exception):
    """Could not find odds for the queried team"""
    def __init__(self, nick):
        self.errmsg = f"{nick}: The API returned this matchup with no odds. ¯\_(ツ)_/¯"

# functions
def FetchLeagueOddsFromAPI(sport_key, bookmaker='unibet', odds_api_key=odds_api_key):
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

def CheckForValidQuery(word_list, nick):
    """
    Checks if the user provided a team and valid league to query.
    
    Parameters
    ----------
    word_list : list
        Every word in the user's message.
    nick : str
        The user's nick.
        
    Returns
    -------
    None
    
    Raises
    ------
    InvalidQuery
        If the user did not provide a team and valid league to query.
    """
    if len(word_list) < 3:
        raise InvalidQuery(nick, sport_key_map)
    league = word_list[1].lower()
    if league not in sport_key_map.keys():
        raise InvalidQuery(nick, sport_key_map)
    return

def WriteNewLeagueOddsFile(sport_key, nick, filepath):
    response = FetchLeagueOddsFromAPI(sport_key)
    if response.status_code != 200:
        raise BadStatusCode(nick, response.status_code)
    else:
        #TODO: check if dir exists first
        with open(filepath, 'w') as file:
            json.dump(response.json(), file)
        print('Remaining requests', response.headers['x-requests-remaining'])
        print('Used requests', response.headers['x-requests-used'])
    return

def LeagueOddsFileIsOld(filepath, minutes=60):
    with open(filepath, 'r') as file: 
        last_modified = stat(filepath).st_mtime
    current_time = time()
    delta = current_time - last_modified
    delta_frac = delta / 60 / minutes
    return True if delta_frac > 1.0 else False

def UpdateLeagueOddsIfNecessary(word_list, nick):
    league = word_list[1]
    sport_key = sport_key_map[league]
    filepath = f"./book-odds/{sport_key}.json"
    if not path.exists(filepath) or LeagueOddsFileIsOld(filepath):
        WriteNewLeagueOddsFile(sport_key, nick, filepath)
    return

def LoadLeagueOdds(word_list):
    league = word_list[1]
    sport_key = sport_key_map[league]
    filepath = f"./book-odds/{sport_key}.json"
    with open(filepath, 'r') as file: 
        league_odds = json.load(file)
    return league_odds

def SearchForGameOdds(word_list, nick, league_odds):
    # inform user if no odds are found
    if len(league_odds) == 0:
        raise NoOddsFound(nick)
    
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
        raise NoGameFound(nick)
    
    return game_odds[0]

def ExtractGameInfo(game_odds, nick):
    tipoff = FormatTimestamp(game_odds['commence_time'])
    home_team = game_odds['home_team']
    away_team = game_odds['away_team']
    
    # fetch market data
    try:
        markets = game_odds['bookmakers'][0]
    except IndexError:
        raise NoGameOddsFound(nick)

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

    return tipoff, away_team, h2h[0], spreads[0], home_team, h2h[1], spreads[1]

def FormatTimestamp(timestamp:str) -> str:
    """Formats a timestamp from the Odds API to CST."""
    tipoff = dt.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    central_tz = tz.gettz('America/Chicago')
    tipoff_cst = tipoff.astimezone(central_tz)
    tipoff_cst = dt.strftime(tipoff_cst, '%a %b %d, %I:%M%p CST')
    return tipoff_cst

def AbbreviateTeamName(team_name):
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

def FormatReply(game_info):
    away_abbrv = AbbreviateTeamName(game_info[1])
    home_abbrv = AbbreviateTeamName(game_info[4])
    matchup = f"{game_info[1]} @ {game_info[4]}"
    moneyline = f"07Moneyline: {away_abbrv} {game_info[2]} {home_abbrv} {game_info[5]}"
    spread = f"09Spread: {away_abbrv} {game_info[3]} {home_abbrv} {game_info[6]}"
    tipoff = game_info[0]
    tipoff_cst = f"14{tipoff}"
    reply = ' | '.join([matchup, moneyline, spread, tipoff_cst])
    return reply

def Sportsbook(msg_obj, pyrc_obj):
    try:
        CheckForValidQuery(msg_obj.word_list, msg_obj.nick)
        UpdateLeagueOddsIfNecessary(msg_obj.word_list, msg_obj.nick)
        league_odds = LoadLeagueOdds(msg_obj.word_list)
        game_odds = SearchForGameOdds(msg_obj.word_list, msg_obj.nick, league_odds)
        game_info = ExtractGameInfo(game_odds, msg_obj.nick)
        reply = FormatReply(game_info)
        return reply, pyrc_obj.channel
    except InvalidQuery as e:
        return e.errmsg, pyrc_obj.channel
    except BadStatusCode as e:
        return e.errmsg, pyrc_obj.channel
    except NoOddsFound as e:
        return e.errmsg, pyrc_obj.channel
    except NoGameFound as e:
        return e.errmsg, pyrc_obj.channel
    except NoGameOddsFound as e:
        return e.errmsg, pyrc_obj.channel

if __name__ == "__main__":
    class testobj:
        def __init__(self):
            self.word_list = ['.sb', 'nba', 'portland']
            self.nick = 'gary'
            self.channel = '#channel'

    to = testobj()
    reply = Sportsbook(to, to)
    print(reply[0])
