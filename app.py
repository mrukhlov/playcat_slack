#!/usr/bin/env python

from slackclient import SlackClient
import time
import requests
import json
import os

def index_getter(letter):
	index = 0
	index_list =[]
	for i in list('kitten'.upper()):
		if i == letter:
			index_list.append(index)
		index+=1
	return index_list


SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
AGENT_TOKEN = os.environ["AGENT_TOKEN"]
BOT_ID = os.environ["BOT_ID"]

slack_client = SlackClient(SLACK_BOT_TOKEN)

def apiai_equest(request):

	global guess_word
	global img_links

	picture = False

	headers = {'Authorization': 'Bearer ' + AGENT_TOKEN,  'Content-Type': 'application/json; charset=utf-8'}
	data = {'query':request, 'lang':'en', 'sessionId':'0000'}
	r = requests.post('https://api.api.ai/api/query?v=20150910', headers=headers, data=json.dumps(data))
	req = json.loads(r.text)

	speech = None
	if req['result']["fulfillment"].has_key('speech'):
		speech = req["result"]["fulfillment"]['speech']

	action = None
	if req['result'].has_key('action'):
		action = req['result']['action']

	if action == 'game.correct_guess' or action == 'game.wrong_guess':
		res, picture = CheckLetter(req)
	elif action == 'game.correct.word':
		guess_word = ['K', '_', '_', '_', '_', 'N']
		res = speech
	elif action == 'confirmation.yes':
		res = speech.replace(' _ _ _ _ ', '____')
	elif action == 'game.start':
		guess_word = ['K', '_', '_', '_', '_', 'N']
		img_links = [
			'https://s22.postimg.org/r9eee4w4d/image.png',
			'https://s22.postimg.org/z3jld9tb1/image.png',
			"https://s22.postimg.org/ih21470d9/image.png"
		]
		res = speech
	else:
		res = None

	return res, action, picture

def CheckLetter(req):

	letter = req['result']['resolvedQuery'].upper()
	letter_index = index_getter(letter)
	letter_diff = [i for i in list('kitten'.upper()) if i not in guess_word]

	picture = True

	if guess_word.count('_') - 1 > -1:
		if guess_word.count(letter) == 0 and letter in letter_diff:
			for i in letter_index:
				guess_word[i] = letter
			if '_' in guess_word:
				output = "That's right! " + ''.join(guess_word) + '. Guess the next one.'
			else:
				output = 'You are so smart! Fantastic! Here is your kitten.'
				global guess_word
				global img_links
				guess_word = ['K', '_', '_', '_', '_', 'N']
		elif letter not in letter_diff and letter in guess_word:
			output = 'You have already guessed this letter. Try again.'
			picture = False
		else:
			output = 'Almost there. Try again!'

	return output, picture
	
def handle_command(command, channel):
	"""
		Receives commands directed at the bot and determines if they
		are valid commands. If so, then acts on the commands. If not,
		returns back what it needs for clarification.
	"""

	text_response, action, picture = apiai_equest(command)
	if text_response != None:

		attachments = []
		link = ''
		if action == 'game.correct.word' or action == 'game.correct_guess':
			if picture:
				if action == 'game.correct.word':
					link = "https://s22.postimg.org/ih21470d9/image.png"
				else:
					if len(img_links) > 0:
						link = img_links[0]
						img_links.remove(link)

				attachments.append({"title": "IMAGE", "image_url": link})

		slack_client.api_call("chat.postMessage", channel=channel, as_user=True, attachments=attachments, text=text_response)



def parse_slack_output(slack_rtm_output):
	"""
		The Slack Real Time Messaging API is an events firehose.
		this parsing function returns None unless a message is
		directed at the Bot, based on its ID.
	"""
	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		#print output_list
		for output in output_list:
			if output and 'text' in output and output['user'] != BOT_ID:
				# return text after the @ mention, whitespace removed
				return output['text'].lower(), output['channel']
	return None, None


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 0.5 # 1 second delay between reading from firehose
	if slack_client.rtm_connect():
		print("StarterBot connected and running!")
		while True:
			command, channel = parse_slack_output(slack_client.rtm_read())
			if command and channel:
				handle_command(command, channel)
			time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print("Connection failed. Invalid Slack token or bot ID?")