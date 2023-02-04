import os

# Paths
USER_LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'user-logs')
ODDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'odds')

# Keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
TWITTER_KEY = os.getenv('TWITTER_KEY')
TWITTER_SECRET = os.getenv('TWITTER_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_TOKEN_SECRET = os.getenv('TWITTER_TOKEN_SECRET')
WOLFRAM_API_KEY = os.getenv('WOLFRAM_API_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Misc
SPAGHETTI_LYRICS = (
    "Lose yourself in Mom's spaghetti. It's ready.",
    "You only get one spaghetti.",
    "Spaghetti only comes once in a lifetime.",
    "Amplified by the fact that I keep on forgetting to make spaghetti.",
    "Tear this motherfucking roof off like two Mom's spaghettis.",
    "Look, if you had Mom's spaghetti, would you capture it, or just let it slip?",
    "There's vomit on his sweater spaghetti, Mom's spaghetti.",
    "He opens his mouth but spaghetti won't come out.",
    "Snap back to spaghetti.",
    "Oh, there goes spaghetti.",
    "He knows he keeps on forgetting Mom's spaghetti.",
    "Mom's spaghetti's mine for the taking.",
    "He goes home and barely knows his own Mom's spaghetti.",
    "Mom's spaghetti's close to post mortem.",
    "No more games. I'ma change what you call spaghetti.",
    "Man these goddamn food stamps don't buy spaghetti.",
    "This may be the only Mom's spaghetti I got.",
    "Make me spaghetti as we move toward a new world order.")
ZODIAC_SIGNS = {'aquarius': '♒ 06Aquarius',
                'pisces': '♓ 04Pisces',
                'aries': '♈ 04Aries',
                'taurus': '♉ 04Taurus',
                'gemini': '♊ 07Gemini',
                'cancer': '♋ 07Cancer',
                'leo': '♌ 08Leo',
                'virgo': '♍ 03Virgo',
                'libra': '♎ 03Libra',
                'scorpio': '♏ 03Scorpio',
                'sagittarius': '♐ 02Sagittarius',
                'capricorn': '♑ 06Capricorn'}
CORRECT_SYNTAX = {'.ask': '.ask [nick]',
                  '.h'  : '.h [sign]',
                  '.wa' : '.wa [query]'}
SPORT_KEY_MAP = {'nfl' : 'americanfootball_nfl',
                 'cfb' : 'americanfootball_ncaaf',
                 'mlb' : 'baseball_mlb',
                 'nhl' : 'icehockey_nhl',
                 'nba' : 'basketball_nba'}
