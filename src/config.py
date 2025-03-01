import pathlib
import os

# paths
PROJECT_WD = pathlib.Path(__file__).resolve().parents[1]
ODDS_DIR = PROJECT_WD / 'data' / 'odds'
print(PROJECT_WD)

# connections
SERVER = "irc.libera.chat"
SSLPORT = "7000"
ADMIN_NICK = "garygreen"
ADMIN_IDENT = "gary"
MAIN_CHANNEL = "##garybot"
GAME_CHANNEL = "##garybot"
IGNORE_LIST = "ChanServ,NickServ,***"
KNOWN_BOTS = "garybot,buttebot,sampre,tercipra,trannybot"

# chatbot
BOT_NICK = "buttebot"
EXIT_CODE = "goodnight"
MODEL = "gemini-2.0-flash"

# keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
WOLFRAM_API_KEY = os.getenv('WOLFRAM_API_KEY')
LLM_KEY = os.getenv('LLM_KEY')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

# misc
CORRECT_SYNTAX = {'.ask': '.ask [nick]',
                  '.h'  : '.h [sign]',
                  '.wa' : '.wa [query]'}
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
SPORT_KEY_MAP = {'nfl' : 'americanfootball_nfl',
                 'cfb' : 'americanfootball_ncaaf',
                 'mlb' : 'baseball_mlb',
                 'nhl' : 'icehockey_nhl',
                 'nba' : 'basketball_nba'}
