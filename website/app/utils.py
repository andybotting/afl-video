import urllib2
import httplib
from urlparse import urlparse

import re
import sys
import logging
import traceback
import datetime, time
import random

import models
import static

from BeautifulSoup import BeautifulStoneSoup
from django.conf import settings
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError

from djangoappengine.utils import on_production_server

URL = "http://www.afl.com.au/ajax.aspx?feed=VideoSearch&videoTabId=%s&videoSubTabId=%s&mid=131673&page=%s"

FEEDS = [	
		{ 'name': 'Match Replays', 'video_id': '616:617', 'tag': 'replay' },
		{ 'name': 'News Desk',	  'video_id': '616:618', 'tag': 'news' },
		{ 'name': 'Highlights',	 'video_id': '616:619', 'tag': 'highlights' },
		{ 'name': 'Panel Shows',	'video_id': '616:620', 'tag': 'panel' },
	]

		#{ 'name': 'Club Video',	 'url': 'http://www.afl.com.au/ajax.aspx?feed=VideoSearch&videoTabId=616&videoSubTabId=621&mid=131673', 'tags': ['club'] },

def check_url(url):
	req = urllib2.Request(url)
	try:
		resp = urllib2.urlopen(req)
	except urllib2.URLError, e:
		if e.code == 404:
			return False
	return True



def check_url1(url):
	o = urlparse(url)
	try:
		conn = httplib.HTTPConnection(o.netloc)
		conn.request("HEAD", o.path)
		resp = conn.getresponse()

		if (resp.status == 200):
			return True

		if (resp.status == 404):
			return False

		if (resp.status == 302):
			if check_url(resp.getheader('location')):
				return True
	except:
		logging.exception("Failed to test URL: %s" % url)
		return False


def update_videos_job():
	for feed in FEEDS:
		for page in range(1,6):
			
			if on_production_server:
				# Build our task url with secret key
				data = "%s_%s_%s" % (feed['tag'], feed['video_id'], page)
				url = "/process_page_%s/%s" % (settings.SECRET_URL_KEY, data)
				logging.info("Adding %s to task queue" % data)
				taskqueue.add(url=url, method="GET")
			else:
				# For debugging only
				process_page(feed['tag'], feed['video_id'], page)

	# Club Video - needs work
	#for team in static.TEAMS:
	#  for stream in team['video_id']:
	#     fetch_pages(team['tags'][:1], stream)


def retag_videos_job():
	video_list = models.Video.objects.all()
	for video in video_list:

		if video.urls[static.QUAL_MED].find("rtsp://") > -1:
			video.delete()
			logging.debug("Video deleted: %s with tags: %s at %s" % (video.name, video.tags, video.urls[static.QUAL_MED]))
		else:
			type = video.get_tag('type')
			video = tag_video(video, type)
			video.save()
			logging.debug("Video found: %s with tags: %s at %s" % (video.name, video.tags, video.urls[static.QUAL_MED]))


def fetch_url(url):
	logging.debug("Fetching URL: %s" % url)
	try:
		req = urllib2.Request(url, None)
		http = urllib2.urlopen(req)
		data = http.read()
		return data
	except:
		logging.error("Could not fetch URL: %s\n%s" % (url, sys.exc_info()[:2]))


def process_page(tag, video_id, page):
	# Split the video_tab_id and video_sub_tabid out
	video_tab_id, video_subtab_id = video_id.split(":")	

	# URL looks like: http://www.afl.com.au/ajax.aspx?feed=VideoSearch&videoTabId=<>&videoSubTabId=<>&mid=131673&page=<>
	url = URL % (video_tab_id, video_subtab_id, page)

	data = fetch_url(url)
	if data:
		# Return true if parsing is successful
		return parse_page(data, tag)


def parse_page(data, type):

	xml = BeautifulStoneSoup(data)
	video_items = xml.findAll("div", { "class" : "video-thumb" } )

	logging.debug("Found %d video items to process" % len(video_items))

	for item in video_items:

		# Find the name and url bits
		video_name = item.img.get('alt')
		video_url = item.a.get('href')

		# Do we already have this url? If not, make a new video object
		video_list = models.Video.objects.filter(urls=video_url)
		if video_list:
			video = video_list[0]
			logging.debug("Found existing video: %s" % (video.name))
		else:
			video = models.Video()
			
		if not check_url(video_url):
			logging.debug("Video %s is a 404! Deleting..." % video_url)
			video.delete()
		else:
			# Set the name
			video.name = video_name
	
			# Set the URLs for each quality
			# Low, Medium and High (0, 1 and 2 respectively)
			video.urls = []
	
			# Test for low quality (172k stream)
			video_low_qual = re.sub("1[mM][bB]{,1}.mp4", "172K.mp4", video_url)
			if check_url(video_low_qual):
				logging.debug("Found low-res video for %s" % video.name)
				video.urls.insert(static.QUAL_LOW, video_low_qual)
			else:
				video.urls.insert(static.QUAL_LOW, None)
	
			# Just blindly insert the medium quality stream
			video.urls.insert(static.QUAL_MED, video_url)
	
			# Test for high quality (2Mb stream)
			video_high_qual = re.sub("1[mM][bB]{,1}.mp4", "2M.mp4", video_url)
			if check_url(video_high_qual):
				logging.debug("Found high-res video for %s" % video.name)
				video.urls.insert(static.QUAL_HIGH, video_high_qual)
			else:
				video.urls.insert(static.QUAL_HIGH, None)
	
			# Lets check to see if a higher res thumbnail is available
			thumbnail_standard = item.img.get('src')
			thumbnail_highres = video.thumbnail.replace('89x50.jpg', '326x184.jpg')
	
			if check_url(thumbnail_highres):
				logging.debug("Found higher-res thumbnail for %s" % video.name)
				video.thumbnail = thumbnail_highres
			elif check_url(thumbnail_standard):
				logging.debug("Found standard-res thumbnail for %s" % video.name)
				video.thumbnail = thumbnail_standard
			else:
				video.thumbnail = "%sthumb/missing-thumb.jpg" % (settings.MEDIA_URL)
	
			# Parse the date
			date_string = item.nextSibling.nextSibling.string
			video.date = datetime.datetime.strptime(date_string, '%m/%d/%Y')
	
			# Apply tags to our video
			video = tag_video(video, type)
		
			# If no errors..	
			if video:
				video.save()
				logging.debug("Video saved: %s with tags: %s at %s" % (video.name, video.tags, video_url))
			else:
				logging.error("Video failed: %s" % video)
	


def tag_video(video, type):
	
	try:
		video_tags = []

		# Get our base URL
		video_url = video.urls[static.QUAL_MED]

		# Apply tag for the feed
		video_tags.append("type:%s" % type)

		# Regex for the match replay URLs
		regex = '.*/(?P<year>\d{4})/ON/iVideo/(?P<game>\w+)/(?P<rnd>\w+)/AFL\d{2}_(?P<round>\w+)_(?P<hometeam>\w+)_vs_(?P<awayteam>\w+)_(?P<qtr>\d)\w{2}_qr.*'
		search = re.search(regex, video_url)

		if search:
			logging.debug("Matched replay game: %s" % video_url)
			result = search.groupdict()
			
			#{'awayteam': 'stk',
			# 'hometeam': 'geel',
 			# 'qtr': '1',
			# 'rnd': 'RD02',
			# 'round': 'FW1',
			# 'type': 'Premiership',
			# 'year': '2010'}

			video_tags.append("game:%s" % result['game'].lower())
			video_tags.append("year:%d" % int(result['year']))
			video_tags.append("qtr:%d" % int(result['qtr']))
			

			# Extract the round number, if it is a normal round, or else it might be a final
			rnd_search = re.search('r[n]{,1}[d]{,1}(\d+)', result['round'], flags=re.IGNORECASE)
			if rnd_search:
				rnd = rnd_search.groups()[0]
				video_tags.append("rnd:%d" % int(rnd))	
			else:
				video_tags.append("rnd:%s" % result['round'].lower())

			for team in static.TEAMS:
				for tag in team['tags']:
					if result['hometeam'] == tag:
						# Only apply the teams first tag. So we don't get bris and bl for brisbane.
						video_tags.append("hometeam:%s" % team['tags'][0])
						video_tags.append("team:%s" % team['tags'][0])
					if result['awayteam'] == tag:
						video_tags.append("awayteam:%s" % team['tags'][0])
						video_tags.append("team:%s" % team['tags'][0])

		else:
			# Matching all non-replay urls

			# Dirty replace hack to prevent regex matching _ as a word char for teams matching
			hacked_video_url = video_url.replace('_','!')

			# Apply tag for the team
			for team in static.TEAMS:
				for tag in team['tags']:
					search = re.search("\W+"+tag+"\W+", hacked_video_url, flags=re.IGNORECASE)
					if search:
						video_tags.append("team:%s" % team['tags'][0]) 

			# Find the year
			year = None
			year_search = re.search('20(\d){2}', video_url)
			if year_search:
				year = year_search.group()
				video_tags.append("year:%s" % year)

			# Match all rounds, including RND1, RND01, RD01, R1, R01 and in both upper and lower case
			rnd = None
			rnd_search = re.search(r"r[n]{,1}[d]{,1}(\d+)", video_url, flags=re.IGNORECASE)
			if rnd_search:
				rnd = rnd_search.groups()[0]
				video_tags.append("rnd:%d" % int(rnd))

			# Match finals weeks
			finals_rnd_search = re.search('FW(\d)', video_url)
			if finals_rnd_search:
				rnd = finals_rnd_search.groups()[0]
				video_tags.append("rnd:fw%d" % int(rnd))

			# Match the quarter 
			# Tested: qtrs = ['qr1','QR01','Q1','Q01','Q_1','QR_2']
			qtr_search = re.search('q[t]{,1}[r]{,1}.{,1}(\d+)', video_url, flags=re.IGNORECASE)
			if qtr_search:
				# Iterate through our qtr matches. Regex has an 'or' so it could be in position [0] or [1]
				for qtr in qtr_search.groups():
					if qtr:
						video_tags.append("qtr:%d" % int(qtr))

			# Exclude Foxtel matches
			foxtel_search = re.search('foxtel', video_url, flags=re.IGNORECASE)
			if foxtel_search:
				video_tags.append("game:foxtel")
		
		video.tags = video_tags
		return video

	except:
		#logging.error("Failed to tag video: %s -- %s: %s (%s)" % (video, sys.exc_info()[:2], traceback.tb_lineno(sys.exc_info()[2])))
		logging.exception("Failed to tag video: %s" % video)


def elapsed_time(seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
	"""
	Takes an amount of seconds and turns it into a human-readable amount of time.
	"""
	# the formatted time string to be returned
	time = []

	# the pieces of time to iterate over (days, hours, minutes, etc)
	# - the first piece in each tuple is the suffix (d, h, w)
	# - the second piece is the length in seconds (a day is 60s * 60m * 24h)
	parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
		(suffixes[1], 60 * 60 * 24 * 7),
		(suffixes[2], 60 * 60 * 24),
		(suffixes[3], 60 * 60),
		(suffixes[4], 60),
		(suffixes[5], 1)]

	# for each time piece, grab the value and remaining seconds, and add it to
	# the time string
	for suffix, length in parts:
		value = seconds / length
		if value > 0:
			seconds = seconds % length
			time.append('%s%s' % (str(value), (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
		if seconds < 1:
			break

	return separator.join(time)

