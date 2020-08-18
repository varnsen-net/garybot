#!/usr/bin/python3
import os
import ssl
import sys
import time
import isodate
import socket
import urllib3
import urllib.parse
from urllib.parse import urlparse
import requests
import threading
import subprocess
import pandas
import random
import re
import csv
import traceback
import tweepy
import html
import pickle
import configparser


## Store local paths
cwd = os.getcwd()
config_path = cwd + "/config.ini"
log_path = cwd + "/chat_log.csv"
error_log_path = cwd + "/error_log.txt"
bankrolls_path = cwd + "/bankrolls.obj"
deckofcards_path = cwd + "/deck_of_cards.csv"

## Server and channel info
config = configparser.ConfigParser()
config.read(config_path)
server = config['connection']['server']
sslport = int(config['connection']['sslport'])
botnick = config['connection']['botnick']
adminnick = config['connection']['adminnick']
adminident = config['connection']['adminident']
channel = config['connection']['channel']
gchan = config['connection']['gchan']

## API keys
youtube_api_key = config['api_keys']['youtube_api_key']
twitter_key = config['api_keys']['twitter_key']
twitter_secret = config['api_keys']['twitter_secret']
twitter_access_token = config['api_keys']['twitter_access_token']
twitter_token_secret = config['api_keys']['twitter_token_secret']
wolfram_api_key = config['api_keys']['wolfram_api_key']


## Errata
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sslsock = ssl.wrap_socket(socket)
exitcode = 'goodnight'
knownbots = ['Supybot','Adjutant','***','garybot',]

def connect():
	print("Connecting to: " + server)
	sslsock.connect((server,sslport))
	irc.sendBytes("USER " + botnick + " " + botnick + " " + botnick + " " + botnick)
	irc.sendBytes("NICK " + botnick)
	irc.sendBytes("JOIN " + channel)

class irc:
	@staticmethod

	def sendBytes(str):
		sslsock.send(bytes(str + "\r\n", "UTF-8"))
		
	def sendMsg(msg, target=channel):
		sslsock.send(bytes('PRIVMSG ' + target + ' :' + msg + '\r\n', 'UTF-8'))

	def pingPong():
		irc.sendBytes('PONG')
		return

	def logMsg(log_path, parsed):
		with open(log_path, "a+", newline="", encoding="utf-8") as log_ref:
			logwriter = csv.writer(log_ref)
			logwriter.writerow(parsed)

	def logError(error_log_path):
		error_timestamp = str(time.asctime())
		with open(error_log_path, "a+", encoding="utf-8") as error_log:
			error_log.write(error_timestamp + "\r\n")
			traceback.print_exc(file=error_log)
			error_log.write("\r\n")

	## Parsing functions
	def parseMessage(str):
		prefix = 'nan'
		command = 'nan'
		parameters = 'nan'
		if str[0] == ':':
			prefix, command, parameters = str.split(' ', 2)
			return prefix, command, parameters
		else:
			return prefix, command, parameters

	def parsePrefix(prefix, command):
		ident = 'nan'
		nick = 'nan'
		commands = ['QUIT','PART','JOIN','NICK','PRIVMSG']
		if command in commands:
			nick, ident = prefix[1:].split('!', 1)
			ident, _ = ident.split('@', 1)
			return nick, ident[1:]
		else:
			ident = prefix[1:]
			return nick, ident

	def parseParameters(parameters, command):
		target = 'nan'
		message = 'nan'
		if command == 'PRIVMSG':
			target, message = parameters.split(' :', 1)
			message = message.strip('\r\n')
			parameters = 'nan'
			return target, message, parameters
		else:
			return target, message, parameters	

class autoreply:
	@staticmethod

	def reasonWillPrevail(message, nick):
		msglower = message.lower()
		if msglower.startswith('imagine unironically'):
			regarded = "".join(random.choice([f.upper(),f]) for f in msglower)
			irc.sendMsg(regarded)
		if 'reason' in msglower:
			irc.sendMsg('REASON WILL PREVAIL')

	def getYouTubeURL(message):
		url = ''
		wordlist = message.split(' ')
		for word in wordlist:
			if 'youtube.com' in word or 'youtu.be' in word:
				url = word
				break
		return url
		
	def getYouTubeID(url):
		video_id = ''
		parsed = urlparse(url)
		if 'youtu.be' in parsed.netloc:
			video_id = parsed.path[1:12]
			return video_id
		elif 'youtube.com' in parsed.netloc:
			if 'v=' in parsed.query:
				_ , video_id = parsed.query.split('v=', 1)
				video_id = video_id[:11]
				return video_id
			elif parsed.query == '':
				video_id = parsed.path.split('/')
				video_id = video_id[2][:11]
				return video_id
			else: 
				return video_id
		else:
			return video_id 

	def getTweet(message, twitter_key, twitter_secret, twitter_access_token, twitter_token_secret):
		statusurl = re.search("twitter.com/\w+/status/\d+", message, re.I)
		if statusurl is not None:
			auth = tweepy.OAuthHandler(twitter_key, twitter_secret)
			auth.set_access_token(twitter_access_token, twitter_token_secret)
			tpy = tweepy.API(auth)
			statusid = re.search("\d{15,}", message, re.I)[0]
			status = tpy.get_status(statusid, tweet_mode="extended")
			name = "04" + status.user.name + ""
			text = "10" + status.full_text.replace("\n", " ") + ""
			text = html.unescape(text)
			date = "14" + str(status.created_at)[:10] + ""
			finalmsg = " | ".join([date, name, text])
			irc.sendMsg(finalmsg)
			#sendMsg("04" + handle + " | 10" + tweet)

	def youTube(message, youtube_api_key):
		if 'youtube.com' in message or 'youtu.be' in message:
			url = autoreply.getYouTubeURL(message)
			video_id = autoreply.getYouTubeID(url)
			api_url = "https://www.googleapis.com/youtube/v3/videos?id="
			urlparams = '&part=snippet,statistics,contentDetails'
			api_key = '&key=' + youtube_api_key
			apiquery = api_url + video_id + api_key + urlparams
			response = requests.get(apiquery).json()
			if len(response['items']) == 0:
				return
			else:
				snippet = response['items'][0]['snippet']
				stats = response['items'][0]['statistics']
				content = response['items'][0]['contentDetails']
				header = '01,00 You00,04Tube '
				title = '26Title: 04' + snippet['title'] + ''
				tdelta = str(isodate.parse_duration(content['duration']))
				duration = '26Duration: 04' + tdelta + '' 
				uploader = '26Uploader: 04' + snippet['channelTitle'] + ''
				uploaded = '26Uploaded: 04' + snippet['publishedAt'][:10] + ''
				views = '26Views: 04' + stats['viewCount'] + ''
				likes = float(stats['likeCount'])
				dislikes = float(stats['dislikeCount'])
				total = likes + dislikes + 1
				like_pct = '26Liked: 04' + str(100 * likes/total)[:2] + '%' + ''
				irc.sendMsg(title + ' | ' + duration + ' | ' + uploader + ' | ' + uploaded + ' | ' + views + ' | ' + like_pct)

class chanfcn:
	@staticmethod

	def checkValidRegex(pattern):
		try:
			re.compile(pattern)
			return True
		except:
			return False

	def makeQueryLog(log):
		qlog = (log
			.query('nick not in @knownbots')
			.query('target == @channel')
			.query('~message.str.startswith("%", na=True)')
			.query('~message.str.startswith("!", na=True)')
			.query('~message.str.startswith("*", na=True)')
			.query('~message.str.startswith(".", na=True)')
		)
		return qlog
		
	def quoteSpaghetti():
		lyrics = [
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
			"Coast-to-coast shows; he blows his own daughter.",
			"No more games. I'ma change what you call spaghetti.",
			"Man these goddamn food stamps don't buy spaghetti.",
			"This may be the only Mom's spaghetti I got.",
			"Make me spaghetti as we move toward a new world order."
		]
		randline = random.choice(lyrics)
		irc.sendMsg(randline)

	def top5(nick, log_path, wordlistlen, message):
		# the user must supply a regular expression to query.
		if wordlistlen < 2:
			reply = nick + ": You did not supply a regex pattern."
			irc.sendMsg(reply)
			return

		# the user must supply a valid regular expression.
		_, userstring = message.strip().split(' ', 1)
		if chanfcn.checkValidRegex(userstring) == False:
			reply = nick + ": You did not supply a valid regex pattern."
			irc.sendMsg(reply)
			return
		
		# we passed the checks, so we're ready to go.
		with open(log_path, "r", encoding="utf-8") as log:
			qlog = pandas.read_csv(
				log, 
				index_col=False,
				na_values = 'nan'
			)
			qlog = chanfcn.makeQueryLog(qlog)
			qlog['found'] = qlog.message.str.count(userstring, re.I)
			qlog = qlog[['nick','found']]
			qlog = (qlog
				.groupby(['nick'])
				.sum()
				.sort_values('found', ascending=False)
				.query('found > 0')
			)
			if len(qlog) == 0:
				reply = nick + ": I found no instances of that string."
				irc.sendMsg(reply)
				return
			else:
				counts = qlog.iloc[:5]
				intlist = list(range(len(counts)))
				stringlist = [str("10" + counts.index[f] + ": 04" + counts.found[f].astype(str) + "") for f in intlist]
				sep = ' | '
				top5string = sep.join(stringlist)
				irc.sendMsg(top5string)

	def askUser(nick, log_path, wordlist, wordlistlen):
		# the user must supply a regular expression to query.
		if wordlistlen < 2:
			reply = nick + ": You did not supply a user to ask."
			irc.sendMsg(reply)
			return

		with open(log_path, "r", encoding="utf-8") as log:
			qlog = pandas.read_csv(
				log, 
				index_col=False,
				na_values = 'nan'
			)
			qlog = chanfcn.makeQueryLog(qlog)
			queriednick = wordlist[1]
			qlog = qlog.query('nick == @queriednick')
			try:
				randomline = random.choice(qlog.message.tolist())
			except:
				reply = nick + ": I could not find a user with that nick."
				irc.sendMsg(reply)
				return
			else:
				reply = "<" + queriednick + "> " + randomline
				irc.sendMsg(reply)

	def countdown():
		for f in ["3", "2", "1"]:
			time.sleep(1.5)
			irc.sendMsg("04" + f)
		time.sleep(1.5)
		irc.sendMsg("03" + "GO GO GO")

	def wolframAlpha(wordlistlen, message, wolfram_api_key):
		# the user must submit a query.
		if wordlistlen < 2:
			reply = nick + ": You didn't ask wolfram anything. Idiot."
			irc.sendMsg(reply)
			return
		
		# send the query to wolfram.
		api_key = '&appid=' + wolfram_api_key
		url = "https://api.wolframalpha.com/v1/result?i="
		_, question = message.split(' ',1)
		question = urllib.parse.quote_plus(question)
		apiquery = url + question + api_key + '&units=metric'
		
		# send the response to the channel.
		response = requests.get(apiquery)
		reply = response.text[:400].replace("\n", "") + '.'
		irc.sendMsg(reply)

class bettor:

	def __init__(self, name, balance):
		self.name = name
		self.balance = balance
		self.handsdealt = 0
		self.coinsflipped = 0
		self.totalwagered = 0.0
		self.totalgains = 0.0
		self.totallosses = 0.0
		self.netprofit = 0.0
		self.vpstate = "idle"
		self.vpbet = 0.0
		self.vphand = []
		self.vpholds = []

	def saveBettors(path, betobjs):
		with open(path, "wb") as rolls:
			pickle.dump(betobjs, rolls)

	def exists(nick, betobjs):
		namelist = []
		for object in betobjs:
			namelist.append(object.name.lower())
		if nick.lower() in namelist:
			return True
		else:
			return False

	def getBettor(nick, betobjs, bankrolls_path):
	# returns an existing user object — or creates a new one if the user isn't
	# already on the books.
		userobj = None
		for object in betobjs:
			if object.name.lower() == nick.lower():
				userobj = object
		if userobj is None:
			userobj = bettor(nick, 10000.00)
			betobjs.append(userobj)
			bettor.saveBettors(bankrolls_path, betobjs)
			return userobj
		else:
			return userobj

	def goodBet(nick, bet, userobj):
		bet_string = str(bet).replace(".", "")
		if bet_string.isnumeric() == False:
			reply = nick + ": Your bet must be a positive real number."
			irc.sendMsg(reply, gchan)
			return False
		elif float(bet) > userobj.balance:
			userbalance = "${:,.2f}".format(userobj.balance)
			reply = nick + ": Insufficient balance. You've only got " + userbalance + " remaining."
			irc.sendMsg(reply, gchan)
			return False
		elif float(bet) < 1:
			reply = nick + ": The minimum bet is $1."
			irc.sendMsg(reply, gchan)
			return False
		else:
			return True

	def stakeMe(nick, betobjs, bankrolls_path):
	# users can reset their balances to $6,900.00 at any time.
		userobj = bettor.getBettor(nick, betobjs, bankrolls_path)
		userobj.balance = 10000.00
		balance = "${:,.2f}".format(userobj.balance)
		reply = nick + ": If you are making money you are losing it — your balance is now 03" + balance
		irc.sendMsg(reply, gchan)
		bettor.saveBettors(bankrolls_path, betobjs)

	def getBalance(nick, wordlistlen, wordlist, betobjs, bankrolls_path):
	# users can check their own balances or the balance of another existing user.
	# if the user's own balance doesn't exist, then we'll create a new user
	# object. if the user is checking a balance that doesn't exist, then we'll
	# reply with an error message. we don't want to let users create unlimited
	# additional users.
		if wordlistlen == 1:
			userobj = bettor.getBettor(nick, betobjs, bankrolls_path)
			reply = bettor.makeBalStr(nick, userobj)
			irc.sendMsg(reply, gchan)
		elif wordlistlen > 1 and bettor.exists(wordlist[1], betobjs):
			userobj = bettor.getBettor(wordlist[1], betobjs, bankrolls_path)
			reply = bettor.makeBalStr(nick, userobj)
			irc.sendMsg(reply, gchan)
		else:
			reply = nick + ": " + wordlist[1] + " is not in the books. You can add yourself using the .reup command."
			irc.sendMsg(reply, gchan)

	def makeBalStr(nick, userobj):
		statdict = {
			"Balance: " : "${:,.2f}".format(userobj.balance),
			"Total wagered: " : "${:,.2f}".format(userobj.totalwagered),
			"Total gains: " : "${:,.2f}".format(userobj.totalgains),
			"Total losses: " : "${:,.2f}".format(userobj.totallosses),
			"Net profit: " : "${:,.2f}".format(userobj.netprofit),
			"Coins flipped: " : str(userobj.coinsflipped),
			"Hands dealt: " : str(userobj.handsdealt),
		}
		statlist = ['' + pair[0] + '03' + pair[1] + '' 
			for pair in statdict.items()]
		reply = nick + ": " + " | ".join(statlist)
		return reply

	def setBalance(nick, ident, adminident, wordlist, betobjs):
		if ident == adminident:
			name = wordlist[1]
			userobj = bettor.getBettor(name, betobjs, bankrolls_path)
			userobj.balance = float(wordlist[2])
			balance = "${:,.2f}".format(userobj.balance)
			reply = nick + ": " + userobj.name + " balance: " + balance
			irc.sendMsg(reply, gchan)
			bettor.saveBettors(bankrolls_path, betobjs)
		elif ident != adminident:
			reply = nick + ": Lmao nice try, but you're not the bot admin."
			irc.sendMsg(reply, gchan)

	def resetBalance(nick, ident, adminident, wordlist, betobjs):
		if ident == adminident:
			name = wordlist[1]
			userobj = bettor.getBettor(name, betobjs, bankrolls_path)
			userobj.handsdealt = 0
			userobj.coinsflipped = 0
			userobj.totalwagered = 0.0
			userobj.totalgains = 0.0
			userobj.totallosses = 0.0
			userobj.netprofit = 0.0
			bettor.saveBettors(bankrolls_path, betobjs)
		elif ident != adminident:
			reply = nick + ": Lmao nice try, but you're not the bot admin."
			irc.sendMsg(reply, gchan)

	def flipCoin():
		states = ["heads", "tails"]
		outcome = random.choice(states)
		return outcome

	def aftermath(bet, payout, userobj, bankobj):
		userobj.balance = round(userobj.balance + payout, 2)
		userobj.totalwagered = round(userobj.totalwagered + float(bet), 2)
		userobj.netprofit = round(userobj.netprofit + payout, 2)
		bankobj.balance = round(bankobj.balance - payout, 2)
		bankobj.totalwagered = round(bankobj.totalwagered + float(bet), 2)
		bankobj.netprofit = round(bankobj.netprofit - payout, 2)

	def betFlips(nick, wordlistlen, wordlist, betobjs):
		userobj = bettor.getBettor(nick, betobjs, bankrolls_path)
		
		# did the user input enough arguments? if not, stop playing.
		if wordlistlen < 3:
			reply = nick + ": The correct syntax is .flip <choice> <wager>."
			irc.sendMsg(reply, gchan)
			return
			
		# did the user make a valid wager? if not, stop playing.
		bet = wordlist[2].replace(",", "")
		if bettor.goodBet(nick, bet, userobj) == False:
			return
			
		# did the user make a valid side selection? if not, stop playing.
		coin_side_choice = wordlist[1].lower()
		if re.match("^h$|^t$", coin_side_choice, re.I) is None:
			reply = nick + ": Use 'h' for heads and 't' for tails."
			irc.sendMsg(reply, gchan)
			return
			
		# if we passed all the checks, then we're ready to play!
		bankobj = bettor.getBettor("Bank", betobjs, bankrolls_path)
		outcome = bettor.flipCoin()
		userobj.coinsflipped = userobj.coinsflipped + 1
		bankobj.coinsflipped = bankobj.coinsflipped + 1
		if coin_side_choice == outcome[0]:
			payout = float(bet) * (100/105)
			bettor.aftermath(bet, payout, userobj, bankobj)
			userobj.totalgains = round(userobj.totalgains + payout, 2)
			bankobj.totallosses = round(bankobj.totallosses + payout, 2)
			userbalance = "${:,.2f}".format(userobj.balance)
			payout = "${:,.2f}".format(payout)
			reply = nick + ": 00,03  " + outcome + "   | Nice! You won 03" + payout + " and your new balance is 03" + userbalance + "."
			irc.sendMsg(reply, gchan)
			bettor.saveBettors(bankrolls_path, betobjs)
		else:
			payout = float(bet) * -1
			bettor.aftermath(bet, payout, userobj, bankobj)
			userobj.totallosses = round(userobj.totallosses - payout, 2)
			bankobj.totalgains = round(bankobj.totalgains - payout, 2)
			userbalance = "${:,.2f}".format(userobj.balance)
			reply = nick + ": 00,04  " + outcome + "   | Better luck next time! Your new balance is 03" + userbalance + "."
			irc.sendMsg(reply, gchan)
			bettor.saveBettors(bankrolls_path, betobjs)
		return
			
	def makeStringOfCards(cardlist):
		cardlist['char'] = 'nan'
		for i in range(0,11):
			if cardlist.suit[i] == "diamonds":
				face = cardlist.face[i]
				cardlist.at[i, 'char'] = "04,00" + face + "♦"
			elif cardlist.suit[i] == "hearts":
				face = cardlist.face[i]
				cardlist.at[i, 'char'] = "04,00" + face + "♥"
			elif cardlist.suit[i] == "spades":
				face = cardlist.face[i]
				cardlist.at[i, 'char'] = "01,00" + face + "♠"
			elif cardlist.suit[i] == "clubs":
				face = cardlist.face[i]
				cardlist.at[i, 'char'] = "01,00" + face + "♣"
		flop = list(cardlist.char[1:6])
		sep = ' '
		flopstring = sep.join(flop)
		return flopstring

	def redrawCards(cardlist, userholdlist):
		for f in [1,2,3,4,5]:
			strf = str(f)
			if strf in str(userholdlist):
				cardlist.iloc[f] = cardlist.iloc[f]
			else:
				cardlist.iloc[f] = cardlist.iloc[f + 6]
		return cardlist

	def getPokerPayout(cardlist):
		finalhand = cardlist[1:6].sort_values('value')
		nuniquesuits = finalhand.suit.nunique()
		facecounts = finalhand.face.value_counts()
		facevaluelist = list(finalhand.value)
		lowcard = min(facevaluelist)
		highcard = max(facevaluelist)
		if facevaluelist == [1,10,11,12,13] and nuniquesuits == 1:
			return "royal flush", 800
		elif facevaluelist == list(range(lowcard, highcard+1)) and nuniquesuits == 1:
			return "straight flush", 50
		elif facecounts[0] == 4:
			return "four-of-a-kind", 25
		elif facecounts[0] == 3 and facecounts[1] == 2:
			return "full house", 9
		elif nuniquesuits == 1:
			return "flush", 6
		elif facevaluelist == list(range(lowcard, highcard+1)) or facevaluelist == [1,10,11,12,13]:
			return "straight", 4
		elif facecounts[0] == 3:
			return "three-of-a-kind", 3
		elif facecounts[0] == 2 and facecounts[1] == 2:
			return "two pair", 2
		elif facecounts[0] == 2 and facecounts.index[0] in ["J","Q","K","A"]:
			return "one pair", 1
		else:
			return "nothing", 0

	def betVideoPoker(nick, wordlist, wordlistlen, betobjs, deckofcards):
		# %vp requires two arguments: 1) "bet" or "hold," and 2) a number for the wagers/holds.
		if wordlistlen < 3:
			reply = nick + ": The video poker command takes two arguments."
			irc.sendMsg(reply, gchan)
			return
		
		# the first argument must be "bet" or "hold".
		if re.match("^b$|^h$", wordlist[1], re.I) is None:
			reply = nick + ": The first argument must be 'b' to bet a new hand, or 'h' to hold card in a current hand."
			irc.sendMsg(reply, gchan)
			return
		
		# the first argument must correspond to the correct user state.
		userobj = bettor.getBettor(nick, betobjs, bankrolls_path)
		if wordlist[1] == "b" and userobj.vpstate != "idle":
			reply = nick + ": You've already got a hand in progress. You must finish the hand you're playing before dealing a new hand."
			irc.sendMsg(reply, gchan)
			return
		elif wordlist[1] == "h" and userobj.vpstate != "waiting_for_holds":
			reply = nick + ": You don't have a hand in progress."
			irc.sendMsg(reply, gchan)
			return

		# the second argument must be a number
		number = wordlist[2].replace(",", "").replace(".", "")
		if number.isnumeric() == False:
			reply = nick + ": The second argument must be a positive real number."
			irc.sendMsg(reply, gchan)
			return

		# if we've passed all the checks, then we're ready to play video poker.
		if wordlist[1] == "b":
			# the bet must be valid.
			bet = wordlist[2].replace(",", "")
			if bettor.goodBet(nick, bet, userobj) == False:
				return
			
			# the bet is valid, so deal a hand.
			cardlist = deckofcards.sample(15).reset_index(drop=True)
			userobj.vphand = cardlist
			userobj.vpbet = float(bet)
			userobj.vpstate = "waiting_for_holds"
			flopstring = bettor.makeStringOfCards(cardlist)
			reply = nick + ": " + flopstring
			irc.sendMsg(reply, gchan)
			bettor.saveBettors(bankrolls_path, betobjs)

		elif wordlist[1] == "h":
			# the user can only hold cards 1-5 (or 0 to hold none).
			if re.match("^[1-5]{1,5}$|^0$", wordlist[2]) is None:
				reply = nick + ": To hold cards 1-5, use numbers 1-5. To hold no cards, use 0."
				irc.sendMsg(reply, gchan)
				return

			# the holds are valid, so redraw and determine the payouts.
			bankobj = bettor.getBettor("Bank", betobjs, bankrolls_path)
			cardlist = userobj.vphand
			userholdlist = wordlist[2]
			cardlist = bettor.redrawCards(cardlist, userholdlist)
			handclass, handmultiplier = bettor.getPokerPayout(cardlist)
			payout = userobj.vpbet * (handmultiplier - 1)
			
			# update money stats.
			bettor.aftermath(userobj.vpbet, payout, userobj, bankobj)
			userobj.handsdealt = userobj.handsdealt + 1
			bankobj.handsdealt = bankobj.handsdealt + 1
			if payout > 0:
				userobj.totalgains = round(userobj.totalgains + payout, 2)
				bankobj.totallosses = round(bankobj.totallosses + payout, 2)
			else:
				userobj.totallosses = round(userobj.totallosses - payout, 2)
				bankobj.totalgains = round(bankobj.totalgains - payout, 2)

			# send end-state info to user.
			flopstring = bettor.makeStringOfCards(cardlist)
			userbalance = "${:,.2f}".format(userobj.balance)
			payout = "${:,.2f}".format(payout + userobj.vpbet)
			reply = nick + ": " + flopstring + " | " + handclass + " | This pays 03" + payout + " (" + str(handmultiplier) + "x multiplier). Your new balance is 03" + userbalance + "."
			irc.sendMsg(reply, gchan)
			
			# reset vp attributes.
			userobj.vpstate = "idle"
			userobj.vpbet = 0.0
			userobj.vphand = []
			userobj.vpholds = []
			bettor.saveBettors(bankrolls_path, betobjs)

def main():
# at its core, main() is a simple while-True loop. sslsock listens for messages
# and sends them through a parser, a logger, and a dictionary of irc functions.
# i call all functions through try-except because i want the bot to continue
# listening in spite of a non-fatal error. we'll log the error for investigation.

	# we'll use a dictionary to call functions given a user trigger.
	gamefcn_dict = {
		".reup" : "bettor.stakeMe(nick, betobjs, bankrolls_path)",
		".bal" : "bettor.getBalance(nick, wordlistlen, wordlist, betobjs, bankrolls_path)",
		".setbal" : "bettor.setBalance(nick, ident, adminident, wordlist, betobjs)",
		".reset" : "bettor.resetBalance(nick, ident, adminident, wordlist, betobjs)",
		".flip" : "bettor.betFlips(nick, wordlistlen, wordlist, betobjs)",
		".vp" : "bettor.betVideoPoker(nick, wordlist, wordlistlen, betobjs, deckofcards)",
	}
	chanfcn_dict = {
		".spaghetti" : "chanfcn.quoteSpaghetti()",
		".top5" : "chanfcn.top5(nick, log_path, wordlistlen, message)",
		".ask" : "chanfcn.askUser(nick, log_path, wordlist, wordlistlen)",
		".wa" : "chanfcn.wolframAlpha(wordlistlen, message, wolfram_api_key)",
		".timer" : "threading.Thread(target=chanfcn.countdown).start()",
	}
	
	# we don't want to generate a list of keys each time we get a message from the server, so let's store them now.
	gamefcn_keys = gamefcn_dict.keys()
	chanfcn_keys = chanfcn_dict.keys()
	
	# if you don't already have a list of bettor objects saved, you can replace the "with open" bit with the following line:
	# betobjs = [bettor("Bank", 10**7), bettor("dummy", 10000.00)]
	with open(bankrolls_path, "r+b") as rolls:
		betobjs = pickle.load(rolls)
	
	# we may as well keep a deck of cards in memory. why not.
	deckofcards = pandas.read_csv(
		deckofcards_path, 
		index_col = False,
	)
	connect()
	irc.sendMsg('connected', adminnick)	
	while True:
		msg = sslsock.recv(4096).decode("UTF-8").strip("\r\n")
		# print(msg) here to output raw irc messages for debugging
		timestamp = time.time()
		if 'PING' in msg:
			irc.pingPong()		
		elif re.match("\:\S+\!", msg):
			try:
				# parse the irc message into useful bits
				prefix, command, parameters = irc.parseMessage(msg)
				nick, ident = irc.parsePrefix(prefix, command)
				target, message, parameters = irc.parseParameters(parameters, command)
				parsed = [command, ident, nick, target, message, parameters, timestamp]
				
				# pay attention to channel specifics/conditions when logging.
				if target == channel and re.match('\D+', command) is not None:
					irc.logMsg(log_path, parsed)
				
				# we'll need to parse the message further for some functions.
				wordlist = message.split(' ')
				wordlist = list(filter(None, wordlist))
				wordlistlen = len(wordlist)
				
				if wordlistlen > 0:
					# quit gracefully
					if target == botnick and nick == adminnick and message == exitcode:
						irc.sendMsg("Goodnight!", adminnick)
						break

					# auto-replies
					if target == channel and nick not in knownbots:
						autoreply.getTweet(message, twitter_key, twitter_secret, twitter_access_token, twitter_token_secret)
						autoreply.youTube(message, youtube_api_key)
						autoreply.reasonWillPrevail(message, nick)

					# call channel-specific functions
					trigger = wordlist[0]
					if trigger in chanfcn_keys and target == channel and nick not in knownbots:
						exec(chanfcn_dict[trigger])
					elif trigger in gamefcn_keys and target == gchan and nick not in knownbots:
						exec(gamefcn_dict[trigger])
			except:
				irc.logError(error_log_path)
				irc.sendMsg("gary, there's been an error.", adminnick)

main()

