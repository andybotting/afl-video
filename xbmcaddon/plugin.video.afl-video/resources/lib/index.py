"""
	Category module: fetches a list of categories to use as folders
"""

# main imports
import sys, os, re, urllib2, urllib
import config

try:
	import xbmc, xbmcgui, xbmcplugin
except ImportError:
	pass 

def make_list():
	try:

		items = []

		# Add the matches and teams lists
		items.append({'name': 'Matches', 'id': 'matches'})
		items.append({'name': 'Teams',   'id': 'teams'})
		
		# Add the other feeds listed in the config file
		for feed in config.FEEDS:
			items.append({'name': feed['name'], 'id': feed['id']})

		# fill media list
		ok = fill_media_list(items)
	except:
		# oops print error message
		print "ERROR: %s (%d) - %s" % (sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
		ok = False

	# send notification we're finished, successfully or unsuccessfully
	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=ok)


def fill_media_list(items):

	try:
		ok = True
		# enumerate through the list of categories and add the item to the media list
		for i in items:
			url = "%s?type=%s" % (sys.argv[0], i['id'])
			#thumbnail = get_thumbnail(c.id)
			icon = "defaultfolder.png"
			listitem = xbmcgui.ListItem(i['name'], iconImage=icon)
			#listitem.setInfo('video',{'episode':s.get_num_episodes()})
			# add the item to the media list

			ok = xbmcplugin.addDirectoryItem(
						handle=int(sys.argv[1]), 
						url=url, 
						listitem=listitem, 
						isFolder=True, 
						totalItems=len(config.FEEDS)
					)

			# if user cancels, call raise to exit loop
			if (not ok): 
				raise

		xbmcplugin.setContent(handle=int(sys.argv[1]), content='tvshows')
	except:
		# user cancelled dialog or an error occurred
		d = xbmcgui.Dialog()
		d.ok('AFL Video Error', 'AFL Video encountered an error:', '  %s (%d) - %s' % (sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ]) )

		# user cancelled dialog or an error occurred
		print "ERROR: %s (%d) - %s" % (sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ],)
		ok = False

	return ok
