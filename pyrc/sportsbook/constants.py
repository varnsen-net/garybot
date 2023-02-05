import os

# Paths
ODDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'odds')

# Keys
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

# Misc
SPORT_KEY_MAP = {'nfl' : 'americanfootball_nfl',
                 'cfb' : 'americanfootball_ncaaf',
                 'mlb' : 'baseball_mlb',
                 'nhl' : 'icehockey_nhl',
                 'nba' : 'basketball_nba'}
