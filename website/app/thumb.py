import os, sys
import logging
from datetime import date, datetime, timedelta

from django.conf import settings
from google.appengine.api import images
from google.appengine.ext import db

import models
import utils

IMAGE_DIR = os.path.join(settings.RESOURCE_DIR,'layer')

def layer(ims, marks, position):
	"""
	imprints a PIL image with the indicated text in lower-right corner
	"""
	side_offset = 20


	# Convert from image data to an image
	im = images.Image(ims)
	mark = images.Image(marks)

	if position == 'left':
		x = side_offset
		y = (im.height - mark.height) / 2
	elif position == 'right':
		x = im.width - mark.width - side_offset
		y = (im.height - mark.height) / 2
	elif position == 'center':
		x = (im.width - mark.width) / 2
		y = (im.height - mark.height) / 2

	result = images.composite(	[(im, 0 ,0, 1.0, images.TOP_LEFT), 
										 (mark, x, y, 1.0, images.TOP_LEFT)],
										 im.width, im.height, 0, images.PNG) 

	return result

def resize(im, dimens):
	w = int(dimens[0])
	h = int(dimens[1])
	result = images.resize(im, w, h, images.PNG)
	return result


def open_image(image):
	fp = os.path.join(IMAGE_DIR, "%s.png" % image)
	logging.debug("Opening file: %s" % fp) 
	f = open(fp)
	img_data = f.read()
	return img_data


def generate_thumb(type, hometeam, awayteam, size):
	logging.debug("Generating thumb: %s_%s_%s_%s" % (type, hometeam, awayteam, size))

	try:
		# Set the grass base image, and overlay the text
		base = open_image('grass')
		text = open_image(type)
		image = layer(base, text, 'center')

		# Home team
		hometeam = open_image(hometeam)
		image = layer(image, hometeam, 'left')

		# Away team
		awayteam = open_image(awayteam)
		image = layer(image, awayteam, 'right')

		dimens = size.split('x')
		image = resize(image, dimens)

		return image
	except:
		logging.exception("Thumbnail error for %s_%s_%s_%s" % (type, hometeam, awayteam, size))


def get_or_generate_thumb(type, hometeam, awayteam, size):
	# Get thumb from cache
	name = "%s_%s_%s_%s" % (type, hometeam, awayteam, size)
	thumb = get_thumb(name)

	# If we have a thumb, check timestamp
	if thumb:
		now = datetime.now()
		generated = thumb.timestamp
		timediff = utils.elapsed_time((now-generated).seconds)
	
		if (now - generated) > timedelta(days=1):
			logging.info("Thumb %s expired %s ago" % (name, timediff))
		else:
			logging.info("Thumb %s found in store that is %s old" % (name, timediff))
			return thumb.img

	# Fall back to generate a new thumb
	img = generate_thumb(type, hometeam, awayteam, size)
	if img:
		save_thumb(img, name)

	return img


def get_thumb(name):
	thumb = db.GqlQuery("SELECT * FROM Thumb WHERE name = :1 LIMIT 1", name).fetch(1)
	if thumb:
		return thumb[0]
	return None


def save_thumb(img, name):
	thumb = get_thumb(name)

	if thumb:
		logging.info("Updating thumb %s in store" % thumb.name)
	else:
		logging.info("Creating new thumb %s in store" % name)
		thumb = models.Thumb()

	thumb.img = img
	thumb.name = name
	thumb.timestamp = datetime.now()
	thumb.save()

