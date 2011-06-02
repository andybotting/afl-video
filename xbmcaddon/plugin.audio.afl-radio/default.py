"""
	Plugin for AFL Radio streams
"""
import xbmc, xbmcgui, xbmcplugin, os
import urllib

URL = "http://lon-cdn220-is-1.se.bptvlive.ngcdn.telstra.com/online-radio-afl_%s|"
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

if ( __name__ == "__main__" ):

	for station in STATIONS:
		name = station['name']
		url = (URL % station['id']) + USER_AGENT
		thumb = THUMB_PATH % station['id']

		listitem = xbmcgui.ListItem(name)
		listitem.setInfo('audio', {"genre": "sport"})
		#listitem.setThumbnailImage(thumb)
		# Add the program item to the list
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem)

	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

