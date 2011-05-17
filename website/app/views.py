import urllib2
import re
import sys
import logging
import datetime, time
import random

import models
import utils
import thumb
import replay_generator

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

from BeautifulSoup import BeautifulStoneSoup
import simplejson


def update_videos_job(request):
	utils.update_videos_job()
	return HttpResponse("OK\n")

def process_page(request):
	# Strip the last part of the URL
	data = request.path.split('/')[-1]

	# Split that last part up by underscore
	tag, video_id, page = data.split('_')

	# Fetch the page
	if utils.process_page(tag, video_id, page):
		return HttpResponse("OK\n")
	else:
		return HttpResponse("Failed\n")


def update_rounds_job(request):
	replay_generator.process_rounds()
	return HttpResponse("OK\n")


def process_round(request):
	data = request.path.split('/')[-1]

	try:
		round = int(data)
	except exceptions.ValueError:
		raise Http404

	replay_generator.process_round(round)
	return HttpResponse("OK\n")


def retag_videos_job(request):
	utils.retag_videos_job()
	return HttpResponse("OK\n")


def get_thumb(request):
	if request.path.endswith('.png'):
		filename = request.path[:-4] # strip extension
		name = filename.split('/')[-1] # Get the url of the image

		# replay_geel_haw.png
		bits = name.split('_')

		if len(bits) != 4:
			raise Http404
		else:
			img_data = thumb.get_or_generate_thumb(bits[0], bits[1], bits[2], bits[3])

		# Return tile
		response = HttpResponse(img_data, mimetype='image/png')
		return response
	else:
		# Invalid url
		raise Http404


def get_videos(request):
	
	query = []
	for k, v in request.GET.iteritems():
		qstring = "%s:%s" % (k, v)
		query.append(qstring)

	logging.debug("Searching Videos for tags: %s" % query)

	if query:
		videos = models.Video.objects.filter(tags=query).order_by("-date")
	else:
		videos = models.Video.objects.all().order_by("-date")[:100]

	return videos


def videos(request):

	query = []
	json = False

	for k, v in request.GET.iteritems():
		if (k == 'output') and (v == 'json'):
			json = True
		else:
			qstring = "%s:%s" % (k, v)
			query.append(qstring)

	logging.debug("Searching Videos for tags: %s" % query)

	if query:
		videos = models.Video.objects.filter(tags=query).order_by("-date")
	else:
		videos = models.Video.objects.all().order_by("-date")[:100]

	if json:
		# Build our JSON result
		result = []
		for video in videos:
			result.append(video.json())

		return HttpResponse(
				simplejson.dumps(result), 
				mimetype="application/json"
			)
	else:
		# Return our web template
		return render_to_response('videos.html', {
					'videos': videos,
				},
				context_instance=RequestContext(request)
			)

def videos_type(request, type):
	videos = models.Video.objects.filter(tags=['type:%s' % type]).order_by("-date")

	return render_to_response('videos.html', {
				'videos': videos,
			},
			context_instance=RequestContext(request)
		)

def video(request, video_id):
	video = models.Video.objects.get(pk=video_id)
	return render_to_response('video.html', {
				'video': video,
			},
			context_instance=RequestContext(request)
		)


def match(request, match_id):
	match = models.Match.objects.get(pk=match_id)

	videos = models.Video.objects.filter(id__in=match.videos)
	logging.debug("List: %s, Videos: %s" % (match.videos, videos))
	match.videos = videos

	return render_to_response('match.html', {
				'match': match,
				'videos': videos,
			},
			context_instance=RequestContext(request)
		)


def matches(request, team=None):
	if team:
		logging.debug("Searching for matches for team: %s" % team)
		matches = models.Match.objects.filter(team=team).order_by("-date")
	else:
		logging.debug("Searching for all matches")
		matches = models.Match.objects.all().order_by("-date")

	logging.debug("Found %d matches" % len(matches))
	return render_to_response('matches.html', {
				'matches': matches,
			},
			context_instance=RequestContext(request)
		)


def team(request, team_id):
	pass


def teams(request):
	# List all the teams
	pass
