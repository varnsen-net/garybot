import sys
import traceback
import configparser
from os import getcwd
from random import choice, random, randint
import pandas as pd
import requests
import urllib
import html
from bs4 import BeautifulSoup

config_path = getcwd() + '/config.ini'
config = configparser.ConfigParser()
config.read(config_path)
wolfram_api_key = config['api_keys']['wolfram_api_key']

spaghetti_lyrics = [
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
	"Make me spaghetti as we move toward a new world order."
]

def quoteSpaghetti(msg_obj, pyrc_obj):
	selection = choice(spaghetti_lyrics)
	response = msg_obj.nick + ": " + selection
	return response, pyrc_obj.channel

def Noisify(response):
	if "pardisfla SUCKS lmao got em" in response:
		noisified = [
			response[randint(0,len(response)-1)]
			if random() < 0.15
			else response[i]
			for i in range(len(response))
		]
		response = "".join(noisified)
	return response

def askUser(msg_obj, pyrc_obj):
	try:
		queried_nick = msg_obj.word_list[1]
		with open(pyrc_obj.log_path + queried_nick + '.csv', "r", encoding="utf-8") as log:
			log = pd.read_csv(
				log, 
				index_col=False,
				usecols = [3],
				squeeze = True,
				header = None,
			)
			sample_log = log.sample(69, replace=True).dropna()
			clean_log = sample_log[~sample_log.str.match('[,.!%]')]
			selection = str(clean_log.sample(1).iloc[0])
			response = '<' + queried_nick + '> ' + selection
			response = Noisify(response)
			return response, pyrc_obj.channel

	except IndexError:
		error_msg = msg_obj.nick + ': ' + 'You did not supply a nick to query.'
		return error_msg, pyrc_obj.channel

	except FileNotFoundError:
		error_msg = msg_obj.nick + ': ' + "I have no record of that user."
		return error_msg, pyrc_obj.channel

def getRandPComment(msg_obj, pyrc_obj):
	url = 'https://pornhub.com/random'
	comments = []
	while len(comments) < 2:
		r = requests.get(url, timeout=6.9)
		soup = BeautifulSoup(
			str(r.content, 'UTF-8', errors='replace'), 
			features="html.parser"
		)
		comments = soup.findAll('div', class_='commentMessage')
		if comments is None:
			comments = []

	comments.pop()
	comments_sanitised = list(map(lambda x : x.find('span').text,comments))
	comment = choice(comments_sanitised)
	response = msg_obj.nick + ': ' + comment
	return response, pyrc_obj.channel

def getHoroscope(msg_obj, pyrc_obj):
	try:
		sign = msg_obj.word_list[1]
		params = (
			('sign', sign.lower()),
			('day', 'today'),
		)

		resp = requests.post('https://aztro.sameerkumar.website/', params=params)
		horoscope = [f.replace('_', ' ').title() + ": " + resp.json()[f] for f in resp.json()]
		description = horoscope[2].split(' ', 1)[1]
		tidbits = ' | '.join(horoscope[3:8])
		response = ' | '.join([description, tidbits])
		return response, pyrc_obj.channel
	except IndexError:
		tb = sys.exc_info()[2]
		extracted = traceback.extract_tb(tb)
		formatted = traceback.format_list(extracted)
		line = formatted[0].splitlines()[1].strip()
		if line.startswith('sign ='):
			error_msg = msg_obj.nick + ': ' + 'You did not supply a sign to query.'
			return error_msg, pyrc_obj.channel
		elif line.startswith('description ='):
			error_msg = msg_obj.nick + ': That is not a valid astrological sign.'
			return error_msg, pyrc_obj.channel

def wolframAlpha(msg_obj, pyrc_obj):
	try:
		# send the query to wolfram.
		api_key = '&appid=' + wolfram_api_key
		url = "https://api.wolframalpha.com/v1/result?i="
		question = msg_obj.message.split(' ',1)[1]
		question = urllib.parse.quote_plus(question)
		apiquery = url + question + api_key + '&units=metric'
		
		# format and return the response
		response = requests.get(apiquery)
		response = msg_obj.nick + ': ' + response.text[:400].replace("\n", "")
		return response, pyrc_obj.channel
	except IndexError:
		error_msg = msg_obj.nick + ': I think you forgot to ask a question.'
		return error_msg, pyrc_obj.channel
		
def getAPOD(msg_obj, pyrc_obj):
	apod_api = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=1"
	apod_data = requests.get(apod_api).json()[0]
	date = apod_data['date']
	title = apod_data['title']
	url = apod_data['hdurl']
	response = '14' + date + ' 04' + title + ': 10' + url
	return response, pyrc_obj.channel



