"""
sportsbook.py  –  IRC .sb command handler
Usage: .sb <league> <city or team name>
       .sb nfl chiefs
       .sb nba los angeles
"""

import os
from datetime import datetime
from time import time

import requests
from dateutil import tz


SPORT_KEYS = {
    'nfl': 'americanfootball_nfl',
    'cfb': 'americanfootball_ncaaf',
    'mlb': 'baseball_mlb',
    'nhl': 'icehockey_nhl',
    'nba': 'basketball_nba',
}

VALID_LEAGUES = ', '.join(SPORT_KEYS)
USAGE = f"Correct syntax is .sb <league> <team>  —  valid leagues: {VALID_LEAGUES}"

BOOKMAKER     = 'draftkings'
CACHE_TTL     = 600  # seconds

_cache: dict = {}  # { sport_key: {'data': [...], 'fetched_at': float} }


def sportsbook(nick, word_list, api_key):
    """
    Handle a .sb IRC command and return the reply string.

    >>> sportsbook('.sb nfl chiefs')
    'Kansas City Chiefs @ ...'

    :param str nick: IRC nick of the user who issued the command.
    :param list word_list: List of command words (e.g. ['.sb', 'nfl', 'chiefs']).
    :param str api_key: API key for The Odds API.
    :return: Reply string to send back to IRC.
    :rtype: str
    """
    if len(word_list) < 3 or word_list[1].lower() not in SPORT_KEYS:
        return f"{nick}: {USAGE}"

    league = word_list[1].lower()
    query  = ' '.join(word_list[2:]).lower()

    games = _get_odds(league, api_key)
    if games is None:
        return f"{nick}: Couldn't fetch odds right now. Try again later."

    game = _find_game(games, query)
    if game is None:
        return f"{nick}: No upcoming {league.upper()} game found for '{query}'."

    reply = _format_reply(game)
    return f"{nick}: {reply}"


def _get_odds(league, api_key):
    """Fetch odds data for the given league, using cache if available.

    :param str league: League key (e.g. 'nfl', 'nba').
    :param str api_key: API key for The Odds API.
    :return: List of games with odds data, or None on failure.
    :rtype: list | None
    """
    sport_key = SPORT_KEYS[league]
    entry = _cache.get(sport_key)

    if entry and (time() - entry['fetched_at']) < CACHE_TTL:
        return entry['data']

    try:
        resp = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                'api_key':    api_key,
                'markets':    'h2h,spreads',
                'oddsFormat': 'american',
                'dateFormat': 'iso',
                'bookmakers': BOOKMAKER,
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    data = resp.json()
    _cache[sport_key] = {'data': data, 'fetched_at': time()}
    return data


def _find_game(games, query):
    """Find the first game where the query matches either team name.

    :param list games: List of game dicts from the API.
    :param str query: Lowercased search query (e.g. 'chiefs').
    :return: Game dict if found, else None.
    :rtype: dict | None
    """
    for game in games:
        if query in game['home_team'].lower() or query in game['away_team'].lower():
            return game
    return None


def _format_reply(game):
    """Format the game and odds information into a reply string.

    :param dict game: Game dict from the API.
    :return: Formatted reply string.
    :rtype: str
    """
    away = game['away_team']
    home = game['home_team']
    tipoff = _fmt_time(game['commence_time'])

    markets = {}
    try:
        for m in game['bookmakers'][0]['markets']:
            markets[m['key']] = {o['name']: o for o in m['outcomes']}
    except (IndexError, KeyError):
        return f"{away} @ {home} | {tipoff} | No odds available"

    def ml(team):
        try:
            price = markets['h2h'][team]['price']
            return f"{price:+d}"
        except KeyError:
            return 'N/A'

    def spread(team):
        try:
            pt = markets['spreads'][team]['point']
            return f"{pt:+g}"
        except KeyError:
            return 'N/A'

    aw, hw = _abbrev(away), _abbrev(home)

    return (
        f"{away} @ {home} | "
        f"{aw} {ml(away)} {hw} {ml(home)} | "
        f"{aw} {spread(away)} {hw} {spread(home)} | "
        f"{tipoff}"
    )


def _fmt_time(ts):
    """Convert ISO timestamp to formatted local time string.

    :param str ts: ISO timestamp (e.g. '2024-09-08T20:20:00Z').
    :return: Formatted time string (e.g. 'Sun Sep 8, 8:20PM CST').
    :rtype: str
    """
    dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.UTC)
    return dt.astimezone(tz.gettz('America/Chicago')).strftime('%a %b %-d, %-I:%M%p CST')


def _abbrev(name):
    """Abbreviate team name to 2-3 letters.

    :param str name: Full team name (e.g. 'Kansas City Chiefs').
    :return: Abbreviated name (e.g. 'KC').
    :rtype: str
    """
    words = name.split()
    if len(words) > 2:
        return ''.join(w[0] for w in words[:2]).upper()
    return words[0][:3].upper()
