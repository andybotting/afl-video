"""
    Plugin for AFL Radio streams
"""
import xbmc, xbmcgui, xbmcplugin, os
import urllib

# urllib.urlencode({'User-Agent':'NSPlayer/11.08.0005.0000'})
URL = "http://lon-cdn220-is-1.se.bptvlive.ngcdn.telstra.com/online-radio-afl_%s|User-Agent=NSPlayer%2F11.08.0005.0000"

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
		{ 'name':'K-Rock Geelong',                    'id':'15' }, ]

if ( __name__ == "__main__" ):

   try:
      ok = True

		for station in STATIONS:
			name = station['name']
			url = URL % station['id']

			#listitem=xbmcgui.ListItem(label=name, iconImage=p.thumbnail, thumbnailImage=p.thumbnail)
			listitem=xbmcgui.ListItem(label=name)
    		listitem.setInfo('audio', {"genre": "sport"})
    		#listitem.setThumbnailImage(os.path.join(os.getcwd(),'icon.png'))
			# Add the program item to the list
			ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False)
