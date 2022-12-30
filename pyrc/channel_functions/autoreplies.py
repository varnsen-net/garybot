import os
import re
import random
import requests
import isodate
import tweepy
import html


# local module
import pyrc.comms as comms


# API keys 
_YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
_TWITTER_KEY = os.getenv('TWITTER_KEY')
_TWITTER_SECRET = os.getenv('TWITTER_SECRET')
_TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
_TWITTER_TOKEN_SECRET = os.getenv('TWITTER_TOKEN_SECRET')
_WOLFRAM_API_KEY = os.getenv('WOLFRAM_API_KEY')
_ODDS_API_KEY = os.getenv('ODDS_API_KEY')
_OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


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


def for_each_url(func):
    """Decorator to apply a function to each youtube or twitter id fetched from
    a user message."""
    def wrapper(ids):
        """Fetch stats from the youtube or twitter api for each id given.

        :param list[str] ids: A list of ids to fetch stats for.
        :returns: None
        :rtype: None
        """
        for id in ids:
            stats = func(id)
            comms.send_message(stats)
        return 
    return wrapper


@for_each_url
def fetch_youtube_stats(video_id, api_key=_YOUTUBE_API_KEY):
    """Fetches stats for a youtube video from googleapis.
    
    :param str video_id: The youtube video id to fetch stats for.
    :param str api_key: The youtube api key.
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


@for_each_url
def fetch_tweet(tweet_id, twitter_key=_TWITTER_KEY,
                twitter_secret=_TWITTER_SECRET,
                twitter_access_token=_TWITTER_ACCESS_TOKEN,
                twitter_token_secret=_TWITTER_TOKEN_SECRET):
    """Fetches a tweet from the twitter api.
    
    :param str tweet_id: The id of the tweet to fetch.
    :param str twitter_key: The twitter api key.
    :param str twitter_secret: The twitter api secret.
    :param str twitter_access_token: The twitter api access token.
    :param str twitter_token_secret: The twitter api token secret.
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


