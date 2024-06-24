#!/usr/bin/env python3

import requests
import re
import json
import os
import subprocess
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

RESET_COLOUR = "\033[0m"
BLOCK_CHARACTERS = ["▂", "▄", "▆", "█"]
VERTICAL_BAR_NORMAL = "|"
TWO_LETTER_NAMES = {
	"LAB": "LB",
	"CON": "CN",
	"REF": "RF",
	"LD": "LD",
	"GRN": "GR",
	"SNP": "SN",
	"PC": "PC",
	"UKIP": "UK",
	"OTH": "OT",
}

#VERTICAL_BAR_TICK = "|"

def getYouGovPolls(pollResults):
	parties = ["CON", "LAB", "LD", "SNP", "PC", "REF", "GRN", "OTH"]
	r = requests.get("https://yougov.co.uk/_pubapis/v5/uk/trackers/voting-intention/overall/")
	data = json.loads(r.text)
	
	numDays = len(data["values"][0]) - 1
	
	firstDay = datetime.strptime("2020-01-26", "%Y-%m-%d")
	latestDay = firstDay + timedelta(days=numDays)
	pollResults["YouGov"]["date"] = latestDay
	
	for i in range(8):
		num = len(data["values"][i])
		pollingData = data["values"][i][num-1]
		pollResults["YouGov"]["results"][parties[i]] = round(pollingData)
	
	return pollResults

def getBBCPolls(pollResults):
	classes = ["party-label--core LAB", "party-label--core CON", "party-label--core REF", "party-label--core LD", "party-label--core GRN", "party-label--core SNP", "party-label--core PC"]
	
	r = requests.get("https://www.bbc.co.uk/news/uk-politics-68079726")
	#f = open("bbc")
	#text = f.read()
	#f.close()
	soup = BeautifulSoup(r.text, features="lxml")
	
	date = soup.find_all("h2", {"class": "chart__title"})[0].text
	dateText = re.findall("[0-9][0-9]? [A-Za-z]* [0-9]{4}", date)[0]
	parsedDate = datetime.strptime(dateText, "%d %B %Y")
	pollResults["BBC"]["date"] = parsedDate
	
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
		#"UKIP": "UKIP",
	}
	
	r = requests.get("https://www.politico.eu/wp-json/politico/v1/poll-of-polls/GB-parliament")
	#f = open("politico")
	#text = f.read()
	#f.close()
	polls = json.loads(r.text)
	lenA = len(polls["trends"]["kalman"])
	latestPolls = polls["trends"]["kalman"][lenA-1]
	
	dateText = latestPolls["date"]
	parsedDate = datetime.strptime(dateText, "%Y-%m-%d")
	pollResults["Politico"]["date"] = parsedDate
	
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

def padStr(x, char=" "):
	if x < 10:
		return char + str(x)
	return str(x)

def roundToBase(x, base):
	return base * round(x/base)

def resetCursor(height):
	moveCursor(-height, -1000)

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

def printScale(offset):
	for x in reversed(range(12)):
		if x % 2 == 0:
			printWithOffset(padStr(x*5) + " " + VERTICAL_BAR_NORMAL, offset)
		else:
			printWithOffset("   " + VERTICAL_BAR_NORMAL, offset)
	resetCursor(13)

def printBottomBar(length, offset):
	moveCursor(12, 0)
	printWithOffset("+" + "-" * length, offset + 3)
	resetCursor(13)		

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

def printData(party, value, offset, colour):
	moveCursor(13, 0)
	printWithOffset(padStr(int(value), char="0"), offset, colour=colour)
	printWithOffset(TWO_LETTER_NAMES[party], offset, colour=colour)
	resetCursor(15)

def printGraph(data, source, colours, hOffset, barSpacing):
	results = sorted(data[source]["results"].items(), key=lambda item: item[1], reverse=True)
	
	formattedDate = datetime.strftime(data[source]["date"], "%d %B %Y")
	printWithOffset(f"{source} ({formattedDate}):", hOffset)
	printScale(hOffset)
	
	graphLen = (barSpacing + 2) * len(results) + barSpacing
	printBottomBar(graphLen, hOffset)
	
	barInitialOffset = hOffset + 4 + barSpacing
	
	for i, (key, val) in enumerate(results):
		printBar(int(val), 2, barInitialOffset + i * (2 + barSpacing), colours[key])
		printData(key, int(val), barInitialOffset + i * (2 + barSpacing), colours[key])
		#notify(key)
	
	return graphLen + 4
	

def renderGraphs(data, config):
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
		"UKIP": "\033[38;2;120;52;115;1m",
		"OTH": "\033[38;2;90;90;90;1m",
	}
	
	
	graph1Len = printGraph(data, "BBC", colours, 0, config["barSpacing"])
	
	secondGraphPadding = graph1Len + config["graphSpacing"]
	if config["rows"] == 3:
		secondGraphPadding = 0
		moveCursor(17, 0)
	graph2Len = printGraph(data, "Politico", colours, secondGraphPadding, config["barSpacing"])
	
	thirdGraphPadding = graph1Len + graph2Len + config["graphSpacing"] * 2
	if config["rows"] > 1:
		thirdGraphPadding = 0
		moveCursor(17, 0)
	printGraph(data, "YouGov", colours, thirdGraphPadding, config["barSpacing"])
	
	moveCursor(17, 0)
	#print(data)
	
	#for key, val in colours.items():
		#print(f"{val}{whiteBackground}{key}{resetColour}")

def getConfig():
	config = {
		"terminalWidth": 0,
		"rows": 1,
		"graphsPerRow": 3,
		"graphSpacing": 1,
		"barSpacing": 2,
	}
	width = os.get_terminal_size().columns
	config["terminalWidth"] = width
	
	# Default,
	if width >= 113:
		return config
	# Reduce graph spacing
	elif width >= 111:
		config["graphSpacing"] = 0
		return config
	# Reduce bar spacing
	elif width >= 87:
		config["graphSpacing"] = 1
		config["barSpacing"] = 1
		return config
	elif width >= 85:
		config["graphSpacing"] = 0
		config["barSpacing"] = 1
		return config
	else:
		print("Error, terminal too narrow")
		exit(1)
		return config
	'''
	elif width >= 74:
		config["rows"] = 2
		return config
	elif width >= 72:
		config["rows"] = 2
		config["graphSpacing"] = 0
		return config
	'''
	
	
	

def run():
	config = getConfig()
	
	pollResults = {
		"BBC": {
			"date": "",
			"results": {},
		},
		"Politico": {
			"date": "",
			"results": {},
		},
		"YouGov": {
			"date": "",
			"results": {},
		},
	}
	pollResults = getBBCPolls(pollResults)
	pollResults = getPoliticoPolls(pollResults)
	pollResults = getYouGovPolls(pollResults)
	#pollResults = {'BBC': {'date': '13 June 2024', 'results': {'LAB': 42, 'CON': 22, 'REF': 14, 'LD': 10, 'GRN': 6, 'SNP': 3, 'PC': 1}}, 'Politico': {'date': '2024-06-10', 'results': {'CON': 21, 'LAB': 44, 'LD': 10, 'GRN': 5, 'SNP': 3, 'REF': 15, 'PC': 1, 'UKP': 1}}}
	renderGraphs(pollResults, config)
	#print(pollResults)

if __name__ == "__main__":
	run()
