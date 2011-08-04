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

from pyamf.remoting.client import RemotingService

URL = "http://www.afl.com.au/ajax.aspx?feed=VideoSearch&videoTabId=%s&videoSubTabId=%s&mid=131673&page=%s"

FEEDS = [	
		{ 'video_id': '616:617', 'tags': {'type': 'replay'} },
		{ 'video_id': '616:618', 'tags': {'type': 'news'} },
		{ 'video_id': '616:619', 'tags': {'type': 'highlights'} },
		{ 'video_id': '616:620', 'tags': {'type': 'panel'} },
		# Geelong Club videos
		{ 'video_id': '191:192', 'tags': {'type': 'club', 'hometeam': 'geel'} },
		{ 'video_id': '191:193', 'tags': {'type': 'club', 'hometeam': 'geel'} },
		{ 'video_id': '191:194', 'tags': {'type': 'club', 'hometeam': 'geel'} },
	]

CHANNELS = [
		{'id':'9',  'name':'Matches',	  'tags': {'type': 'replay'}},
		{'id':'10', 'name':'Newsdesk',	 'tags': {'type': 'news'}},
		{'id':'11', 'name':'Highlights',   'tags': {'type': 'highlights'}},
		{'id':'13', 'name':'Panel Shows',  'tags': {'type': 'panel'}},
		{'id':'62', 'name':'Geelong TV',   'tags': {'type': 'club', 'hometeam': 'geel'}},
]

class AEST(datetime.tzinfo):
	def utcoffset(self, dt):
		return datetime.timedelta(hours=10)
	def dst(self, dt):
		return datetime.timedelta(0)


def tags_to_string(tags):
	tag_strings = []
	for k,v in tags.items():
		tag_strings.append("%s:%s" % (k,v))
	return ",".join(tag_strings)


def string_to_tags(string):
	tags = {}
	tag_strings = string.split(",")
	for tag in tag_strings:
		k,v = tag.split(":")
		tags[k] = v
	return tags

def hms_to_seconds(string):
	seconds = None
	if string:
		arr = string.split(':')
		if len(arr) == 3:
			seconds = (int(arr[0])*60*60) + (int(arr[1])*60) + int(arr[2])
	return seconds


def check_url(url):
	test = 0
	attempts = 3
	while test < attempts:
		code = http_test(url)
		logging.debug("URL %s gave code: %d" % (url, code))
		if code != 0:
			return code;
		else:
			test = test + 1
	# Fail
	logging.error("URL %s failed %d checks" % (url, attempts))
	return 0

def http_test(url):
	code = 0
	try:
		o = urlparse(url)
		conn = httplib.HTTPConnection(o.netloc, timeout=10)
		conn.request("HEAD", o.path)
		resp = conn.getresponse()

		# 302 redirect
		if (resp.status == 302):
			url = resp.getheader('location')
			return check_url(url)
		else:
			code = resp.status
	except:
		logging.exception("Failed to test URL: %s" % url)

	return code


def get_service_data(service, method, params):
	logging.debug("Fetching AMF data for: %s" % params)
	data = None
	attempts = 3
	while attempts > 0:
		data = amf_service(service, method, params)
		if data:
			logging.debug("AMF service returned data: %s" % (data))
			return data
		else:
			attempts = attempts - 1
	logging.error("Failed to fetch data from AMF Service" % params)
	return None


def amf_service(service, method, params):
	data = None
	try:
		srv = getattr(service, method)
		data = srv(params)
		if data != False:
			return data
	except:
		logging.exception("AMF service failed for: %s" % params)


def update_videos_job():
	for channel in CHANNELS:

		data = "%s_%s" % (channel['id'], tags_to_string(channel['tags']))

		if on_production_server:
			# Build our task url with secret key
			url = "/process_channel_%s/%s" % (settings.SECRET_URL_KEY, data)
			logging.info("Adding %s to task queue" % data)
			taskqueue.add(url=url, method="GET")
		else:
			# For debugging only
			logging.info("Fetching page %s" % data)
			process_channel(channel['id'], channel['tags'])



def process_channel(channel_id, tags):
	client = RemotingService('http://afl.bigpondvideo.com/App/AmfPhp/gateway.php')	
	service = client.getService('Miscellaneous')
	params = {'navId':channel_id, 'startRecord':'0', 'howMany':'15', 'platformId':'1', 'phpFunction':'getClipList', 'asFunction':'publishClipList'}
	videos_list = get_service_data(service, 'getClipList', params)
	for video_item in videos_list[0]['items']:
		#try:
		parse_video(video_item['content'], tags)
		#except:
		#	logging.error("Error parsing video: %s\n%s" % (video_item['content']['contentId'], sys.exc_info()[:2]))


def parse_video(video_item, tags):

	# {'invokeName': u'AFL', 'description': u'A great passage of team play is sealed with a goal', 'stateId': u'3', 'title': u'Wojo finishes with class', 'contentId': u'367011', 'imageUrl': u'20110626152716a_89x50.png', 'channelId': u'1', 'duration': u'00:00:21', 'channelName': u'AFL'}

	video_list = models.Video.objects.filter(video_id=video_item['contentId'])
	if video_list:
		video = video_list[0]
		logging.debug("Found existing video: %s" % (video.name))
		video_high_qual = video.urls[static.QUAL_HIGH]
	else:
		client = RemotingService('http://afl.bigpondvideo.com/App/AmfPhp/gateway.php')
		service = client.getService('SEOPlayer')
		video_high_qual = get_service_data(service, 'getMediaURL', {'cid':video_item['contentId']})

		if video_high_qual:
			# Do we already have this url? If not, make a new video object
			video_list = models.Video.objects.filter(urls=video_high_qual)
			if video_list:
				video = video_list[0]
				logging.debug("Found existing video: %s" % (video.name))
			else:
				video = models.Video()
				video.date = datetime.datetime.now(AEST())
			
	code = check_url(video_high_qual)
	if code == 404:
		logging.debug("Video %s is a 404! Deleting..." % video_high_qual)
		video.delete()
	else:
		logging.debug("Video %s is HTTP code: %d" % (video_high_qual, code))
		# Set the name
		video.name = video_item['title']
		video.description = video_item['description']
		video.video_id = video_item['contentId']
		video.duration = hms_to_seconds(video_item['duration'])

		# Set the URLs for each quality
		# Low, Medium and High (0, 1 and 2 respectively)
		video.urls = []

		# Test for low quality (172k stream)
		video_low_qual = re.sub("2[mM][bB]{,1}.mp4", "172K.mp4", video_high_qual)
		video_med_qual = re.sub("2[mM][bB]{,1}.mp4", "1M.mp4", video_high_qual)

		if check_url(video_low_qual) != 404:
			logging.debug("Using high and low res video for %s" % video.name)
			video.urls.insert(static.QUAL_LOW, video_low_qual)
			video.urls.insert(static.QUAL_MED, video_med_qual)
		else:
			video.urls.insert(static.QUAL_LOW, None)
			video.urls.insert(static.QUAL_MED, None)

		# Just blindly insert the medium quality stream
		video.urls.insert(static.QUAL_HIGH, video_high_qual)

		# Lets check to see if a higher res thumbnail is available
		thumbnail_standard = "http://bigpondvideo.com/web/images/content/%s" % video_item['imageUrl']
		thumbnail_highres = thumbnail_standard.replace('89x50.jpg', '326x184.jpg')

		if check_url(thumbnail_highres) == 200:
			logging.debug("Found higher-res thumbnail for %s" % video.name)
			video.thumbnail = thumbnail_highres
		else:
			logging.debug("Using standard-res thumbnail for %s" % video.name)
			video.thumbnail = thumbnail_standard


		# Apply tags to our video
		video = tag_video(video, tags)

		# If no errors..	
		if video:
			video.save()
			logging.debug("Video saved: %s with tags: %s at %s" % (video.name, video.tags, video_high_qual))
		else:
			logging.error("Video failed: %s" % video)




def update_videos_job_old():
	for feed in FEEDS:
		for page in range(1,5):
			
			data = "%s_%s_%s" % (feed['video_id'], page, tags_to_string(feed['tags']))

			if on_production_server:
				# Build our task url with secret key
				url = "/process_page_%s/%s" % (settings.SECRET_URL_KEY, data)
				logging.info("Adding %s to task queue" % data)
				taskqueue.add(url=url, method="GET")
			else:
				# For debugging only
				logging.info("Fetching page %s" % data)
				process_page(feed['tags'], feed['video_id'], page)


def retag_videos_job():
	video_list = models.Video.objects.all()
	for video in video_list:

		if video.urls[static.QUAL_MED].find("rtsp://") > -1:
			video.delete()
			logging.debug("Video deleted: %s with tags: %s at %s" % (video.name, video.tags, video.urls[static.QUAL_MED]))
		else:
			video = tag_video(video, tags=[])
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


def process_page_old(tags, video_id, page):
	# Split the video_tab_id and video_sub_tabid out
	video_tab_id, video_subtab_id = video_id.split(":")	

	# URL looks like: http://www.afl.com.au/ajax.aspx?feed=VideoSearch&videoTabId=<>&videoSubTabId=<>&mid=131673&page=<>
	url = URL % (video_tab_id, video_subtab_id, page)

	data = fetch_url(url)
	if data:
		# Return true if parsing is successful
		return parse_page(data, tags)


def parse_page(data, tags):

	xml = BeautifulStoneSoup(data)
	video_items = xml.findAll("div", { "class" : "video-thumb" } )

	logging.debug("Found %d video items to process" % len(video_items))

	for item in video_items:

		# Find the name and url bits
		video_name = item.img.get('alt')

		# Get the URL
		onclick = item.a.get('onclick')
		video_id_search = re.search('PlayVideo\(\'(\d+)\',', onclick)
		if video_id_search:
			video_id = video_id_search.groups()[0]

			logging.debug("Found Video with ID: %s" % video_id)

			# AMF call to get the URL from the content id.
			client = RemotingService('http://afl.bigpondvideo.com/App/AmfPhp/gateway.php')
			amf_service = client.getService('SEOPlayer')
			video_high_qual = amf_service.getMediaURL({'cid':video_id})

		# Do we already have this url? If not, make a new video object
		video_list = models.Video.objects.filter(urls=video_high_qual)
		if video_list:
			video = video_list[0]
			logging.debug("Found existing video: %s" % (video.name))
		else:
			video = models.Video()
			
		code = check_url(video_high_qual)
		if code == 404:
			logging.debug("Video %s is a 404! Deleting..." % video_high_qual)
			video.delete()
		else:
			logging.debug("Video %s is HTTP code: %d" % (video_high_qual, code))
			# Set the name
			video.name = video_name
			video.video_id = video_id
	
			# Set the URLs for each quality
			# Low, Medium and High (0, 1 and 2 respectively)
			video.urls = []
	
			# Test for low quality (172k stream)
			video_low_qual = re.sub("2[mM][bB]{,1}.mp4", "172K.mp4", video_high_qual)
			video_med_qual = re.sub("2[mM][bB]{,1}.mp4", "1M.mp4", video_high_qual)
			if check_url(video_low_qual) != 404:
				logging.debug("Using high and low res video for %s" % video.name)
				video.urls.insert(static.QUAL_LOW, video_low_qual)
				video.urls.insert(static.QUAL_MED, video_med_qual)
			else:
				video.urls.insert(static.QUAL_LOW, None)
				video.urls.insert(static.QUAL_MED, None)
	
			# Just blindly insert the medium quality stream
			video.urls.insert(static.QUAL_HIGH, video_high_qual)
	
			# Lets check to see if a higher res thumbnail is available
			thumbnail_standard = item.img.get('src')
			thumbnail_highres = thumbnail_standard.replace('89x50.jpg', '326x184.jpg')
	
			if check_url(thumbnail_highres) == 200:
				logging.debug("Found higher-res thumbnail for %s" % video.name)
				video.thumbnail = thumbnail_highres
			else:
				logging.debug("Using standard-res thumbnail for %s" % video.name)
				video.thumbnail = thumbnail_standard
	
			# Parse the date
			date_string = item.nextSibling.nextSibling.string
			video.date = datetime.datetime.strptime(date_string, '%d/%m/%Y')
	
			# Apply tags to our video
			video = tag_video(video, tags)
		
			# If no errors..	
			if video:
				video.save()
				logging.debug("Video saved: %s with tags: %s at %s" % (video.name, video.tags, video_high_qual))
			else:
				logging.error("Video failed: %s" % video)
	


def tag_video(video, tags):
	
	try:
		# Get our base URL
		video_url = video.urls[static.QUAL_HIGH]

		# Assign the initial tags
		for k,v in tags.items():
			video.add_tag(k, v)

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

			video.add_tag("game", result['game'].lower())
			video.add_tag("year", int(result['year']))
			video.add_tag("qtr", int(result['qtr']))
			

			# Extract the round number, if it is a normal round, or else it might be a final
			rnd_search = re.search('r[n]{,1}[d]{,1}(\d+)', result['round'], flags=re.IGNORECASE)
			if rnd_search:
				rnd = rnd_search.groups()[0]
				video.add_tag("rnd", int(rnd))
			else:
				video.add_tag("rnd", result['round'].lower())

			# Tag the home and away teams for match replays
			for team in static.TEAMS:
				for tag in team['tags']:
					if result['hometeam'] == tag:
						# Only apply the teams first tag. So we don't get bris and bl for brisbane.
						video.add_tag("hometeam", team['tags'][0])
					if result['awayteam'] == tag:
						video.add_tag("awayteam", team['tags'][0])

		else:
			# Matching all non-replay urls

			# Dirty replace hack to prevent regex matching underscore as a word char for teams matching
			hacked_video_url = video_url.replace('_','!')

			# Apply tag for the team
			for team in static.TEAMS:
				for tag in team['tags']:
					search = re.search("\W+"+tag+"\W+", hacked_video_url, flags=re.IGNORECASE)
					if search:
						if not video.has_tag("hometeam"):
							video.add_tag("hometeam", team['tags'][0]) 
						else:
							video.add_tag("awayteam", team['tags'][0]) 

			# Find the year from the URL
			#year = None
			#year_search = re.search('20(\d){2}', video_url)
			#if year_search:
			#	year = year_search.group()
			#	video.add_tag("year:%s" % year)

			# More reliable way of getting the year
			year = video.date.year
			video.add_tag("year", year)
			

			# Match all rounds, including RND1, RND01, RD01, R1, R01 and in both upper and lower case
			rnd = None
			rnd_search = re.search(r"ro?u?n?d\s?(\d{1,2})", video_url, flags=re.IGNORECASE)
			if rnd_search:
				rnd = rnd_search.groups()[0]
				video.add_tag("rnd", int(rnd))

			# Match finals weeks
			finals_rnd_search = re.search('FW(\d)', video_url)
			if finals_rnd_search:
				rnd = finals_rnd_search.groups()[0]
				video.add_tag("rnd", "fw%d" % int(rnd))

			# Match the quarter 
			# Tested: qtrs = ['qr1','QR01','Q1','Q01','Q_1','QR_2']
			qtr_search = re.search('q[t]{,1}[r]{,1}.{,1}(\d+)', video_url, flags=re.IGNORECASE)
			if qtr_search:
				# Iterate through our qtr matches. Regex has an 'or' so it could be in position [0] or [1]
				for qtr in qtr_search.groups():
					if qtr:
						video.add_tag("qtr", int(qtr))

			# Exclude Foxtel matches
			foxtel_search = re.search('foxtel', video_url, flags=re.IGNORECASE)
			if foxtel_search:
				video.add_tag("game", "foxtel")
		
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

