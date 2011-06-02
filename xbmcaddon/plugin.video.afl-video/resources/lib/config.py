import os

version = '0.1.0'

SERVER = "http://afl-video.appspot.com"
#SERVER = "http://localhost:8000"

VIDEOS_URL = SERVER + "/video/"
MATCHES_URL = SERVER + '/matches/?output=json'
MATCH_URL = SERVER + "/video/match/%s/?output=json"

# Video quality
QUAL_LOW = 0
QUAL_MED = 1
QUAL_HIGH = 2

TEAMS = [
		{  'name': 'Adelaide',            'id': 'adel' },
		{  'name': 'Brisbane',            'id': 'bl' },
		{  'name': 'Carlton',             'id': 'carl' },
		{  'name': 'Collingwood',         'id': 'coll' },
		{  'name': 'Essendon',            'id': 'ess' },
		{  'name': 'Fremantle',           'id': 'fre' },
		{  'name': 'Gold Coast',          'id': 'gcfc' },
		{  'name': 'Geelong',             'id': 'geel' },
#		{  'name': 'Greater West Sydney', 'id': 'gws' },
		{  'name': 'Hawthorn',            'id': 'haw' },
		{  'name': 'Melbourne',           'id': 'melb' },
		{  'name': 'North Melbourne',     'id': 'nmfc' },
		{  'name': 'Port Adelaide',       'id': 'port' },
		{  'name': 'Richmond',            'id': 'rich' },
		{  'name': 'St. Kilda',           'id': 'stk' },
		{  'name': 'Sydney',              'id': 'syd' },
		{  'name': 'West Coast',          'id': 'wce' },
		{  'name': 'Western Bulldogs',    'id': 'wb' },
	]


FEEDS = [
		{ 'name': 'Match Replays', 'id': 'replay',     'url': SERVER + '/video/?output=json&type=replay' },
		{ 'name': 'News Desk',     'id': 'news',       'url': SERVER + '/video/?output=json&type=news' },
		{ 'name': 'Highlights',    'id': 'highlights', 'url': SERVER + '/video/?output=json&type=highlights' },
		{ 'name': 'Panel Shows',   'id': 'panel',      'url': SERVER + '/video/?output=json&type=panel' },
	]

