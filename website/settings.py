# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
from djangoappengine.settings_base import *

import os

# Uncomment this if you're using the high-replication datastore.
# TODO: Once App Engine fixes the "s~" prefix mess we can remove this.
#DATABASES['default']['HIGH_REPLICATION'] = True

# Activate django-dbindexer for the default database
DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
DBINDEXER_SITECONF = 'dbindexes'

SECRET_KEY = '=r-$b*8halm+358&5t046hlm6-&6-3d3vfc4(a7yd0dbrakhvi'

# Used in URLs for cron jobs
SECRET_URL_KEY = 'I2bmxS2RAfVmt7C3DBeNHh75Ugqfc66xYFc5tT8JYrW53QDq8rYVGADK'

INSTALLED_APPS = (
	'app',
	'django.contrib.admin',
	'django.contrib.contenttypes',
	'django.contrib.auth',
	'django.contrib.sessions',
	'djangotoolbox',
	'dbindexer',

	# djangoappengine should come last, so it can override a few manage.py commands
	'djangoappengine',
)

MIDDLEWARE_CLASSES = (
	# This loads the index definitions, so it has to come first
	'dbindexer.middleware.DBIndexerMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.contrib.auth.context_processors.auth',
	'django.core.context_processors.request',
	'django.core.context_processors.media',
)

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_DIR = (os.path.join(os.path.dirname(__file__), 'media'),)
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

# Image layers
RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'resources')

# Media URL
MEDIA_URL = "/media/"

ROOT_URLCONF = 'urls'

