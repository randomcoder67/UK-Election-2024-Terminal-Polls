# UK Election 2024 Terminal Polls

A simple Python script to display current average UK election polling in the terminal.

Pulls poll data from the [BBC Election Tracker](https://www.bbc.co.uk/news/uk-politics-68079726) and the [Politico Poll of Polls](https://www.politico.eu/europe-poll-of-polls/united-kingdom/). 

(Note, UKIP is only present in the politico graph as the BBC doesn't have polling data for them)

## Usage

`python3 polling.py` will display the polling data in the terminal

## Notes

The colours used for each party are not the [exact party colours](https://en.wikipedia.org/wiki/Wikipedia:Index_of_United_Kingdom_political_parties_meta_attributes), I used the ones from Politico instead as they are easier to read.

The BBC graph will probably stop working once the election is over, I'll probably remove it then as I don't think the BBC normally have that data outside of election time.

[Make sure you are registered to vote before the deadline on the 18th June](https://www.gov.uk/register-to-vote)
