from django.db import models
from djangotoolbox import fields
from google.appengine.ext import db
import datetime
import static

class Match(models.Model):
	hometeam = models.CharField(max_length=4)
	awayteam = models.CharField(max_length=4)
	date = models.DateField()
	round = models.IntegerField()
	# premiership, finals, grandfinal, nabcup, foxtelcup
	type = models.CharField(max_length=16)
	videos = fields.ListField(models.IntegerField())
	thumbnail = models.URLField(max_length=256)
	afl_id = models.IntegerField(null=True)

	def __str__(self):
		return self.get_title()

	def get_season(self):
		season = ""
		if self.type == 'premiership':
			season = "AFL %d Season" % self.date.year
		elif self.type == 'final':
			season = "AFL %d Finals" % self.date.year
		elif self.type == 'grandfinal':
			season = "AFL %d Grand Final" % self.date.year
		return season

	def get_round(self):
		round = ""
		if self.type == 'final':
			round = "Week %d" % self.round
		else:
			round = "Round %d" % self.round
		return round

	def get_teams(self):
		for team in static.TEAMS:
			if self.hometeam == team['id']:
				hometeam = team['name']
			if self.awayteam == team['id']:
				awayteam = team['name']
		return "%s v %s" % (hometeam, awayteam)	

	def get_title(self):
		season = self.get_season()
		round = self.get_round()
		return "%s %s %s " % (season, round, self.get_teams())	

	def get_thumb_name(self):
		return ("replay_%s_%s.png" % (self.hometeam, self.awayteam))

	def json(self):

		return {	
				'id': self.pk,
				'name': self.get_title(), 
				'videos': self.videos, 
				'thumbnail': self.get_thumb_name(), 
				'date': self.date.strftime("%Y-%m-%d"), 
				'type': self.type,
				'season': self.get_season(),
				'round': self.get_round(), 
			}




class Video(models.Model):
	name = models.CharField(max_length=64)
	video_id = models.CharField(max_length=8)
	urls = fields.ListField(models.CharField(max_length=512))
	thumbnail = models.URLField(verify_exists=True, max_length=256)
	description = models.CharField(max_length=512, null=True)
	date = models.DateField()
	duration = models.IntegerField(null=True)
	tags = fields.ListField(models.CharField(max_length=16))

	class Admin:
		list_display   = ('name', 'thumbnail', 'date')
		ordering	   = ('-date',)
		search_fields  = ('name',)

	def __str__(self):
		return self.name

	def get_tags(self):
		d = {}
		for t in self.tags:
			k,v = t.split(':')
			d[k] = v
		return d

	def get_tag(self, tag):
		tags = self.get_tags()
		if tags.has_key(tag):
			return tags[tag] 

	def has_tag(self, tag):
		tags = self.get_tags()
		if tags.has_key(tag):
			return True
		return False

	def add_tag(self, k, v):
		new_tags = []
		tags = self.get_tags()
		tags[k] = v

		for l,w in tags.items():
			if l == 'hometeam':
				new_tags.append("hometeam:%s" % w)
				new_tags.append("team:%s" % w)
			elif l == 'awayteam':
				new_tags.append("awayteam:%s" % w)
				new_tags.append("team:%s" % w)
			else:
				new_tags.append("%s:%s" % (l, w))

		self.tags = new_tags

	def json(self):

		urls = {}
		if self.urls[static.QUAL_LOW]:
			urls['low'] = self.urls[static.QUAL_LOW]
		if self.urls[static.QUAL_MED]:
			urls['med'] = self.urls[static.QUAL_MED]
		if self.urls[static.QUAL_HIGH]:
			urls['high'] = self.urls[static.QUAL_HIGH]


		return {	
				'name': self.name, 
				'urls': urls, 
				'thumbnail': self.thumbnail, 
				'date': self.date.strftime("%Y-%m-%d"), 
				'tags':self.tags
			}


class Thumb(db.Model):
	name = db.StringProperty()
	img = db.BlobProperty()
	timestamp = db.DateTimeProperty()
