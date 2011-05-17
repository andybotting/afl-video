import os, sys
import simplejson as json
import urllib2
import datetime
import re
import logging

import static
import models
import utils

from django.conf import settings
from google.appengine.api.labs import taskqueue
from djangoappengine.utils import on_production_server

def fetch_url(url):
	"""	Simple function that fetches a URL using urllib2.
		An exception is raised if an error (e.g. 404) occurs.
	"""
	print("Fetching URL: %s" % url)
	http = urllib2.urlopen(urllib2.Request(url, None, ))
	return http.read()


def process_rounds():
	# 744 = Round 1, 2010
	# 754 = Round 10, 2010
	# 780 = Round 4, 2011
	for rndreq in range(780,785):
		if on_production_server:
			# Build our task url with secret key
			url = "/process_round_%s/%s" % (settings.SECRET_URL_KEY, rndreq)
			logging.info("Adding %s to task queue" % rndreq)
			taskqueue.add(url=url, method="GET")
		else:
			process_round(rndreq)

def process_round(rnd):
	xml_url = "http://xml.afl.com.au/feed.aspx?format=json&feed_getfixturebyround=req2&param_req2_round=%d" % rnd
	data = fetch_url(xml_url)
	process_round_data(data)


def get_or_new_video(video_url):
	# Do we already have this url? If not, make a new video object
	video_list = models.Video.objects.filter(urls=video_url)
	if video_list:
		video = video_list[0]
		print("Found existing video: %s" % video.name)
	else:
		video = models.Video()

	return video


def get_or_new_match(afl_id):
	# Do we already have this url? If not, make a new video object
	match_list = models.Match.objects.filter(afl_id=afl_id)
	if match_list:
		match = match_list[0]
		print("Found existing match: %s" % match)
	else:
		match = models.Match()

	return match


def process_round_data(data):
	j = json.loads(data) 
	items = j['dataFeederResponse']['req2']['row']
	for item in items:
		try:
			date = datetime.datetime.strptime(item['LocalStartTime'], "%d/%m/%Y %I:%M:%S %p")
			year = int(date.year)
			short_year = date.strftime('%y')
			round = int(item['RoundName'].split(" ")[-1])
			round_pad = "%02d" % round
			round_string = "RD%s" % round_pad
			round_short = round_string
			round_name = item['RoundName']
			home_id = item['HomeTeamReference'].lower()
			away_id = item['AwayTeamReference'].lower()
			afl_id = int(item['Id'])
			final = False

			# Set the game type
			if item['SeasonName'].find('Final') > -1:
				type = 'final'
				round_string = "FinalsW%d" % round
				round_short = "FW%d" % round
				final = True
			else:
				type = 'premiership'

			# Set the teams
			for team in static.TEAMS:
				if team['id'] == home_id:
					home_val = team['val']
					home_name = team['name']
				if team['id'] == away_id:
					away_val = team['val']
					away_name = team['name']

			# Create a new match
			match = get_or_new_match(afl_id)
			match.hometeam = home_id
			match.awayteam = away_id
			match.date = date
			match.round = round
			match.type = type
			match.afl_id = afl_id
			match.thumbnail = '/img/thumb-match.jpg'
		
			match_videos = []

			if year < 2011 and round < 10 and not final:

				video_url_med = "http://pd.streaming.telstra.com/pd_afl0/OnDemand/%d/ON/iVideo/Premiership/%s/NV_%s_%sV%s_1M.mp4" % (year, round_string, round_string.title(), home_val, away_val)
				if utils.check_url(video_url_med):
					video = get_or_new_video(video_url_med)
					video.name = "%s %s %s v %s" % (round_string.title(), year, home_name, away_name)
					video.thumbnail = "%sthumb/match-replay.jpg" % (settings.MEDIA_URL) 
					video.date = date
					video.urls = []

					# Test for low quality (172k stream)
					video_low_qual = re.sub("1[mM][bB]{,1}.mp4", "172K.mp4", video_url_med)
					if utils.check_url(video_low_qual):
						print("Found low-res video for %s" % video.name)
						video.urls.insert(static.QUAL_LOW, video_low_qual)
					else:
						video.urls.insert(static.QUAL_LOW, None)

					# Just blindly insert the medium quality stream
					video.urls.insert(static.QUAL_MED, video_url_med)

					# Test for high quality (2Mb stream)
					video_high_qual = re.sub("1[mM][bB]{,1}.mp4", "2M.mp4", video_url_med)
					if utils.check_url(video_high_qual):
						print("Found high-res video for %s" % video.name)
						video.urls.insert(static.QUAL_HIGH, video_high_qual)
					else:
						video.urls.insert(static.QUAL_HIGH, None)

					video = utils.tag_video(video, 'replay')
					print("Saving video: %s" % video)
					video.save()

					match_videos.append(video.pk)

			else:
				for i, qtr in enumerate(['1st','2nd','3rd','4th']):
					video_url_med = "http://bptvpd.ngcdn.telstra.com/pd_afl0/OnDemand/%d/ON/iVideo/Premiership/%s/AFL%s_%s_%s_vs_%s_%s_qr_full_1M.mp4" % (year, round_string, short_year, round_short.lower(), home_id, away_id, qtr)

					if utils.check_url(video_url_med):
						video = get_or_new_video(video_url_med)

						if final:
							video.name = "%s %s %s v %s (%s Qtr)" % (round_name, year, home_name, away_name, qtr)
						else:
							video.name = "%s %s %s v %s (%s Qtr)" % (round_string.title(), year, home_name, away_name, qtr)

						video.thumbnail = "%sthumb/match-replay-%s-qtr.jpg" % (settings.MEDIA_URL, qtr)
						video.date = date
						video.urls = []

						# Test for low quality (172k stream)
						video_low_qual = re.sub("1[mM][bB]{,1}.mp4", "172K.mp4", video_url_med)
						if utils.check_url(video_low_qual):
							print("Found low-res video for %s" % video.name)
							video.urls.insert(static.QUAL_LOW, video_low_qual)

						# Just blindly insert the medium quality stream
						video.urls.insert(static.QUAL_MED, video_url_med)

						# Test for high quality (2Mb stream)
						video_high_qual = re.sub("1[mM][bB]{,1}.mp4", "2M.mp4", video_url_med)
						if utils.check_url(video_high_qual):
							print("Found high-res video for %s" % video.name)
							video.urls.insert(static.QUAL_HIGH, video_high_qual)

						video = utils.tag_video(video, 'replay')
						print("Saving video: %s" % video)
						video.save()

						match_videos.append(video.pk)

			match.videos = match_videos
			print("Saving match: %s" % match.get_title())
			r = match.save()
		except Exception, e:
			logging.exception("Failed to parse match")

if __name__ == "__main__" :
	process_rounds()
