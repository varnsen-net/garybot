from os import getcwd
import re
import random
import requests
import isodate
from urllib.parse import urlparse, parse_qs, urljoin
import tweepy
import html
import configparser
from typing import Pattern

import pyrc.comms as comms
import pyrc.constants as const


# connection config
kconf = const.irc_config['API_keys']


def imagine_without_iron(message):
    """Randomize the case of each letter of the user's message.
    
    :param str message: The user's message.
    :returns: None
    :rtype: None
    """
    random_cased = "".join(random.choice([f.upper(),f]) for f in message)
    comms.send_message(random_cased)
    return


def reason_will_prevail() -> None:
    """Duh."""
    comms.send_message('REASON WILL PREVAIL')
    return 


def find_youtube_ids(message, dotbe_regex=const.YOUTU_DOTBE_REGEX,
                     dotcom_regex=const.YOUTUBE_DOTCOM_REGEX):
    """Search the user's message for valid youtube urls using the compiled
    regexes locacted in constants.py.
    
    :param str message: The user's message.
    :param Pattern[str] dotbe_regex: The compiled regex to match youtube.be urls.
    :param Pattern[str] dotcom_regex: The compiled regex to match youtube.com urls.
    :returns: A list of youtube video ids.
    :rtype: list[str]
    """
    video_ids = []
    if (dotbe_matches := dotbe_regex.findall(message)):
        video_ids.extend(dotbe_matches)
    if (dotcom_matches := dotcom_regex.findall(message)):
        video_ids.extend(dotcom_matches)
    return video_ids


def get_youtube_stats(video_id, api_key=kconf['youtube_api_key']):
    """Fetches stats for a youtube video from googleapis.
    
    :param str video_id: The youtube video id to fetch stats for.
    :param str api_key: The youtube api key fetched from config.ini.
    :returns: A string containing stats on the youtube video.
    :rtype: str
    """
    path = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'id' : video_id,
        'key' : api_key,
        'part' : 'snippet,statistics,contentDetails'
    }
    response = requests.get(path, params).json()
    snippet = response['items'][0]['snippet']
    stats = response['items'][0]['statistics']
    content = response['items'][0]['contentDetails']

    # compose reply
    parts = {
        'Title' : snippet['title'],
        'Duration' : str(isodate.parse_duration(content['duration'])),
        'Uploader' : snippet['channelTitle'],
        'Uploaded' : snippet['publishedAt'][:10],
        'Views' : stats['viewCount'],
        'Likes' : stats['likeCount'],
    }
    parts_fmted = [f'26{e}: 04{parts[e]}' for e in parts.keys()]
    header = '01,00 You00,04Tube '
    response = ' | '.join([header] + parts_fmted)
    return response


def send_youtube_stats(video_ids):
    """Fetch stats from the youtube api for each video id and send it to the
    channel.

    :param list[str] video_ids: A list of youtube video ids.
    :returns: None
    :rtype: None
    """
    for video_id in video_ids:
        stats = get_youtube_stats(video_id)
        comms.send_message(stats)
    return


def find_tweet_ids(message, twitter_regex=const.TWITTER_REGEX):
    """Search the user's message for valid twitter urls using the compiled
    regexes locacted in constants.py.
    
    :param str message: The user's message.
    :param Pattern[str] twitter_regex: The compiled regex to match twitter urls.
    :returns: A list of tweet ids.
    :rtype: list[str]
    """
    tweet_ids = []
    if (matches := twitter_regex.findall(message)):
        tweet_ids.extend(matches)
    return tweet_ids


def fetch_tweet(tweet_id, twitter_key=kconf['twitter_key'],
                twitter_secret=kconf['twitter_secret'],
                twitter_access_token=kconf['twitter_access_token'],
                twitter_token_secret=kconf['twitter_token_secret']):
    """Fetches a tweet from the twitter api.
    
    :param str tweet_id: The id of the tweet to fetch.
    :param str twitter_key: The twitter api key fetched from config.ini.
    :param str twitter_secret: The twitter api secret fetched from config.ini.
    :param str twitter_access_token: The twitter api access token fetched from config.ini.
    :param str twitter_token_secret: The twitter api token secret fetched from config.ini.
    :returns: A string containing the tweet.
    :rtype: str
    """
    auth = tweepy.OAuthHandler(twitter_key, twitter_secret)
    auth.set_access_token(twitter_access_token, twitter_token_secret)
    tpy = tweepy.API(auth)
    status = tpy.get_status(tweet_id, tweet_mode="extended")
    header = '00,02 Twitter '
    name = f"15{status.user.name}"
    text = status.full_text.replace('\n', ' ')
    text = f"02{text}"
    text = html.unescape(text)
    date = f"14{str(status.created_at)[:10]}"
    response = " | ".join([header, date, name, text])
    return response


def send_tweet_stats(tweet_ids):
    """Fetch tweets from the twitter api for each tweet id and send it to the
    channel.

    :param list[str] tweet_ids: A list of tweet ids.
    :returns: None
    :rtype: None
    """
    for tweet_id in tweet_ids:
        tweet = fetch_tweet(tweet_id)
        comms.send_message(tweet)
    return


# def autoResponses(msg_obj, pyrc_obj):
	# msglower = msg_obj.message.lower()
	# responses = [
		# imagineWithoutIron(msglower),
		# reasonWillPrevail(msglower),
		# getYouTubeStats(msg_obj.word_list, youtube_api_key),
		# getTweet(msg_obj.message, twitter_key, twitter_secret, twitter_access_token, twitter_token_secret),
	# ]
	# [pyrc_obj.sendMsg(r, pyrc_obj.channel) for r in responses if r is not None]


