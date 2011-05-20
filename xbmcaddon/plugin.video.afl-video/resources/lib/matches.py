import sys
import config
import utils
import comm

try:
	import xbmc, xbmcgui, xbmcplugin
except ImportError:
	pass # for PC debugging

def make_list():
	#params = utils.get_url(url)	

	try:
		# Show a dialog
		pDialog = xbmcgui.DialogProgress()
		pDialog.create('AFL Video', 'Getting Episode List')
		pDialog.update(50)

		matches = comm.fetch_matches()

		# fill media list
		ok = fill_match_list(matches)
	except:
		# oops print error message
		print "ERROR: %s (%d) - %s" % (sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
		ok = False

	# send notification we're finished, successfully or unsuccessfully
	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=ok)


def fill_match_list(matches):

	try:	
		ok = True

		for m in matches:
			listitem = xbmcgui.ListItem(label=m.title, iconImage=m.thumbnail, thumbnailImage=m.thumbnail)
			url = "%s?match=%s" % (sys.argv[0], m.id)
			#listitem.setInfo('video', m.get_xbmc_list_item())

			# Add the item to the list
			ok = xbmcplugin.addDirectoryItem(
						handle = int(sys.argv[1]),
						url = url,
						listitem = listitem,
						isFolder = True,
						totalItems = len(config.FEEDS)
					)
					

		#xbmcplugin.setContent(handle=int(sys.argv[1]), content='episodes')
	except:
		# user cancelled dialog or an error occurred
		print "ERROR: %s (%d) - %s" % ( sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
		ok = False

	return ok
