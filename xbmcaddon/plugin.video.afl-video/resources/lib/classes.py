import os
import re
import utils
import datetime
import urllib
import time
import config

import xbmcaddon
__addon__ = xbmcaddon.Addon(os.path.basename(os.getcwd()))


class Match(object):
	def __init__(self):
		self.id = 0
		self.title = ''
		self.videos = []
		self.thumbnail = ''
		self.date = datetime.datetime.now()
		self.type = '' # premiership, finals, grandfinal, nabcup, foxtelcup
		self.season = ''
		self.description = ''
		self.round = ''
		self.genre = 'Sports'
		self.rating = 'PG'
		self.duration = '00:30:00'

	def __repr__(self):
		return self.title

	def add_video(self, video):
		self.videos.append(video)

	def get_date(self):
		return self.date.strftime("%Y-%m-%d")

	def get_year(self):
		return self.date.year

	def get_url(self):
		# http://afl-video.appspot.com/video/match/dddd/?output=json
		return config.MATCH_URL % self.id

	def get_xbmc_list_item(self):
		""" Returns a dict of program information, in the format which
			XBMC requires for video metadata.
		"""
		info_dict = {	'tvshowtitle': self.title,
							'title': self.title,
							'genre': self.genre,
							'plot': self.description,
							'plotoutline': self.description,
							'duration': self.duration,
							'year': self.get_year(),
							'aired': self.get_date(),
							'season': self.get_year(),
							'mpaa': self.rating, }

		return info_dict



class Video(object):

	def __init__(self):
		self.id = -1
		self.title = ''
		self.category = 'Sport'
		self.keywords = []
		self.rating = 'PG'
		self.description = None
		self.duration = None
		self.season = None
		self.date = datetime.datetime.now()
		self.thumbnail = ''
		self.urls = []

	def __repr__(self):
		return self.title

	def __cmp__(self, other):
		return cmp(self.title, other.title)

	def get_title(self):
		""" Return a string of the title, nicely formatted for XBMC list
		"""
		title = self.title
		return title

	def get_description(self):
		""" Return a string the program description, after running it through
			the descape.
		"""
		return utils.descape(self.description)

	def get_category(self):
		""" Return a string of the category. E.g. Comedy
		"""
		return utils.descape(self.category)

	def get_rating(self):
		""" Return a string of the rating. E.g. PG, MA
		"""
		return utils.descape(self.category)

	def get_duration(self):
		""" Return a string representing the duration of the program.
			E.g. 00:30 (30 minutes)
		"""
		return self.duration

	def get_date(self):
		""" Return a string of the date in the format 2010-02-28
			which is useful for XBMC labels.
		"""
		return self.date.strftime("%Y-%m-%d")

	def get_year(self):
		""" Return an integer of the year of publish date
		"""
		return self.date.year

	def get_season(self):
		""" Return an integer of the Series, discovered by a regular
			expression from the orginal title, unless its not available,
			then a 0 will be returned.
		"""
		if self.season is None:
			return self.get_year()
		return int(self.season)

	def get_url(self):
		""" Return the URL for the video. If the requested quality is
			not available, then we give the default, which is medium.
		"""
		quality = int(__addon__.getSetting('quality'))
		url = self.urls[quality]
		print url
		if url is None:
			url = self.urls[config.QUAL_MED]
		return url


	def get_xbmc_list_item(self):
		""" Returns a dict of program information, in the format which
			XBMC requires for video metadata.
		"""
		info_dict = {	'title': self.get_title(),
						'genre': self.get_category(),
						'year': self.get_year(),
						'aired': self.get_date(),
						'season': self.get_season(), }

		if self.duration: 
			info_dict['duration'] = self.get_duration()
		
		if self.description:
			info_dict['plot'] = self.get_description()

		return info_dict

