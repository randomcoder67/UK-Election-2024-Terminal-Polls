#!/usr/bin/env python3

import requests
import re
import json
import subprocess
from bs4 import BeautifulSoup

RESET_COLOUR = "\033[0m"
BLOCK_CHARACTERS = ["▂", "▄", "▆", "█"]
VERTICAL_BAR_NORMAL = "|"
#VERTICAL_BAR_TICK = "|"

def getBBCPolls(pollResults):
	classes = ["party-label--core LAB", "party-label--core CON", "party-label--core REF", "party-label--core LD", "party-label--core GRN", "party-label--core SNP", "party-label--core PC"]
	
	r = requests.get("https://www.bbc.co.uk/news/uk-politics-68079726")
	#f = open("bbc")
	#text = f.read()
	#f.close()
	soup = BeautifulSoup(r.text, features="lxml")
	
	date = soup.find_all("h2", {"class": "chart__title"})[0].text
	dateText = re.findall("[0-9][0-9]? [A-Za-z]* [0-9]{4}", date)[0]
	pollResults["BBC"]["date"] = dateText
	
	for c in classes:
		a = soup.find_all("li", {"class": c})
		li = a[0]
		div = li.findChildren("div")[0]
		partyName = div.findChildren("span", {"class": "party-label__party"})[0].text
		poll = div.findChildren("span", {"class": "party-label__value"})[0].text
		#print(partyName, poll)
		pollResults["BBC"]["results"][partyName] = int(poll.replace("%", ""))
	return pollResults

def getPoliticoPolls(pollResults):
	# Politico has UKIP, BBC doesn't
	# Also names are different, converting them here
	
	polToApprv = {
		"Con": "CON",
		"Lab": "LAB",
		"LibDem": "LD",
		"Green": "GRN",
		"SNP": "SNP",
		"BP": "REF",
		"PLPW": "PC",
		"UKIP": "UKP",
	}
	
	r = requests.get("https://www.politico.eu/wp-json/politico/v1/poll-of-polls/GB-parliament")
	#f = open("politico")
	#text = f.read()
	#f.close()
	polls = json.loads(r.text)
	lenA = len(polls["trends"]["kalman"])
	latestPolls = polls["trends"]["kalman"][lenA-1]
	
	pollResults["Politico"]["date"] = latestPolls["date"]
	for key, val in polToApprv.items():
		pollResults["Politico"]["results"][val] = round(latestPolls["parties"][key])
	
	return pollResults

def moveCursor(down, right):
	if down < 0:
		print("\033[" + str(abs(down)) + "A", end="")
	elif down > 0:
		print("\033[" + str(down) + "B", end="")
	if right < 0:
		print("\033[" + str(abs(right)) + "D", end="")
	elif right > 0:
		print("\033[" + str(right) + "C", end="")

def printWithOffset(string, offset, colour=""):
	moveCursor(0, -1000)
	moveCursor(0, offset)
	print(f"{colour}{string}{RESET_COLOUR}")

def padStr(x):
	if x < 10:
		return " " + str(x)
	return str(x)

def roundToBase(x, base):
	return base * round(x/base)

def resetCursor(height):
	moveCursor(-height, -1000)

def printScale(offset):
	for x in reversed(range(12)):
		if x % 2 == 0:
			printWithOffset(padStr(x*5) + " " + VERTICAL_BAR_NORMAL, offset)
		else:
			printWithOffset("   " + VERTICAL_BAR_NORMAL, offset)
	resetCursor(13)

def printBottomBar(length, offset):
	moveCursor(12, 0)
	printWithOffset("+" + "-" * (length * 4 + 2), offset + 3)
	resetCursor(13)

def notify(i):
	subprocess.run(["notify-send", str(i)])

def getBlockChar(height):
	if height <= 1.25:
		return BLOCK_CHARACTERS[0]
	elif height <= 2.5:
		return BLOCK_CHARACTERS[1]
	elif height <= 3.75:
		return BLOCK_CHARACTERS[2]
	else:
		return BLOCK_CHARACTERS[3]
		

def printBar(value, width, offset, colour):
	moveCursor(1, 0)
	
	for x in reversed(range(0, 55, 5)):
		if x < value:
			#printWithOffset(str(x), offset, colour=colour)
			height = roundToBase(value - x, 1.25)
			barChar = getBlockChar(height)
			printWithOffset(barChar * width, offset, colour=colour)
		else:
			#printWithOffset(str(x), offset, colour=colour)
			print("")
	
	resetCursor(12)

def printGraph(data, source, colours, hOffset):
	results = sorted(data[source]["results"].items(), key=lambda item: item[1], reverse=True)
	printWithOffset(f"{source} ({data[source]['date']}):", hOffset)
	printScale(hOffset)
	printBottomBar(len(results), hOffset)
	for i, (key, val) in enumerate(results):
		printBar(int(val), 2, hOffset + 6 + i * 4, colours[key])
		#notify(key)
	

def renderGraphs(data):
	# https://superuser.com/questions/1713969/how-to-put-colors-in-terminal
	#printf '\e[38;2;240;100;200m\e[48;2;200;255;50mHello World!\e[0m\n'
	resetColour = "\033[0m"
	whiteBackground = "\033[48;2;224;224;224m"
	whiteBackground = ""
	#bold = "\033[31;1"
	colours = {
		"LAB": "\033[38;2;240;0;28;1m",
		"CON": "\033[38;2;33;117;217;1m",
		"REF": "\033[38;2;41;219;201;1m",
		"LD": "\033[38;2;255;127;0;1m",
		"GRN": "\033[38;2;88;171;39;1m",
		"SNP": "\033[38;2;250;205;80;1m",
		"PC": "\033[38;2;70;163;92;1m",
		"UKP": "\033[38;2;120;52;115;1m",
	}
	printGraph(data, "BBC", colours, 0)
	printGraph(data, "Politico", colours, 40)
	moveCursor(17, 0)
	#print(data)
	
	#for key, val in colours.items():
		#print(f"{val}{whiteBackground}{key}{resetColour}")

def run():
	pollResults = {
		"BBC": {
			"date": "",
			"results": {},
		},
		"Politico": {
			"date": "",
			"results": {},
		},
	}
	pollResults = getBBCPolls(pollResults)
	pollResults = getPoliticoPolls(pollResults)
	#pollResults = {'BBC': {'date': '13 June 2024', 'results': {'LAB': 42, 'CON': 22, 'REF': 14, 'LD': 10, 'GRN': 6, 'SNP': 3, 'PC': 1}}, 'Politico': {'date': '2024-06-10', 'results': {'CON': 21, 'LAB': 44, 'LD': 10, 'GRN': 5, 'SNP': 3, 'REF': 15, 'PC': 1, 'UKP': 1}}}
	renderGraphs(pollResults)
	#print(pollResults)

if __name__ == "__main__":
	run()
