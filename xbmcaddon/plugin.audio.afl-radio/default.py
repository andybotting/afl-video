"""
	Plugin for AFL Radio streams
"""
import xbmc, xbmcgui, xbmcplugin, os
import urllib

HOST = "fli-cdn220-is-1.se.bptvlive.ngcdn.telstra.com"
URL = "http://" + HOST + "/online-radio-afl_%s|"
USER_AGENT = urllib.urlencode({'User-Agent':'NSPlayer/11.08.0005.0000'})
THUMB_PATH = os.path.join(os.getcwd(), "img", "radio_%s.jpg")

# Stations list
STATIONS = [
		{ 'name':'SEN Melbourne',                     'id':'1' },
		{ 'name':'ABC774',                            'id':'2' },
		{ 'name':'5AA Adelaide',                      'id':'3' },
		{ 'name':'6PR Perth',                         'id':'4' },
		{ 'name':'3AW Melbourne',                     'id':'5' },
		{ 'name':'National Indigenous Radio Service', 'id':'6' },
		{ 'name':'Gold FM Gold Coast',                'id':'7' },
		{ 'name':'Triple M Sydney',                   'id':'11' },
		{ 'name':'Triple M Melbourne',                'id':'12' },
		{ 'name':'Triple M Brisbane',                 'id':'13' },
		{ 'name':'Triple M Adelaide',                 'id':'14' },
		{ 'name':'K-Rock Geelong',                    'id':'15' },
	]

__handle__ = int(sys.argv[1])

def get_params(s):
	dict = {}
	pairs = s.lstrip("?").split("&")
	for pair in pairs:
		if len(pair) < 3: continue
		kv = pair.split("=",1)
		k = kv[0]
		v = urllib.unquote_plus(kv[1])
		dict[k] = v
	return dict

def make_params(d):
	pairs = []
	for k,v in d.iteritems():
		k = urllib.quote_plus(k)
		v = urllib.quote_plus(str(v))
		pairs.append("%s=%s" % (k,v))
	return "&".join(pairs)

def list_stations():
	for station in STATIONS:
		thumb = THUMB_PATH % station['id']
		listitem = xbmcgui.ListItem(station['name'])
		labels = { "title": station['name'], "genre": "Sport" }
		listitem.setInfo('audio', infoLabels=labels)
		listitem.setThumbnailImage(thumb)
		params = make_params({"id": station['id'], "name": station['name']})
		url = "%s?%s" % (sys.argv[0], params)
		xbmcplugin.addDirectoryItem(handle=__handle__, url=url, listitem=listitem)

	xbmcplugin.endOfDirectory(handle=__handle__, succeeded=True)

def play(params):
	p = get_params(params)

	pDialog = xbmcgui.DialogProgress()
	pDialog.create('AFL Radio', 'Starting ' +  p['name'], 'Please wait, this might take a while...')
	pDialog.update(50)

	thumb = THUMB_PATH % p['id']
	labels = { "title": p['name'], "genre": "Sport" }
	listitem = xbmcgui.ListItem(p['name'])
	listitem.setInfo('audio', infoLabels=labels)
	listitem.setThumbnailImage(thumb)
	url = 'http://fli-cdn220-is-1.se.bptvlive.ngcdn.telstra.com/online-radio-afl_' + p['id'] + '?WMBitrate=262144|' + urllib.urlencode({'User-Agent':'NSPlayer/11.08.0005.0000'})
	xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, listitem)
	pDialog.close()


if __name__ == "__main__" :
	params = sys.argv[2]
	p = get_params(params)

	if p.has_key("id"):
		play(params)
	else:
		list_stations()

