from configparser import ConfigParser
import re


# read config
config_path = './config.ini' # assumes config is in same dir as main script
irc_config = ConfigParser()
irc_config.read(config_path)

# regular expressions
YOUTU_DOTBE_REGEX = re.compile(r"youtu\.be/([\w\d]{11})")
YOUTUBE_DOTCOM_REGEX = re.compile(r"youtube\.com/watch\?v=([\w\d]{11})")
TWITTER_REGEX = re.compile(r"twitter\.com/\w+/status/(\d+)")


