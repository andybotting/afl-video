import sys
import config
import utils
import comm

try:
	import xbmc, xbmcgui, xbmcplugin
except ImportError:
	pass # for PC debugging

def make_list(url):
	params = utils.get_url(url)	

	try:
		# Show a dialog
		pDialog = xbmcgui.DialogProgress()
		pDialog.create('AFL Video', 'Getting Team List')

		# fill media list
		ok = fill_media_list(programs)
	except:
		# oops print error message
		print "ERROR: %s (%d) - %s" % (sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
		ok = False

	# send notification we're finished, successfully or unsuccessfully
	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=ok)


def fill_media_list(programs):

	try:	
		ok = True

		for p in programs:
			listitem=xbmcgui.ListItem(label=p.get_title(), iconImage=p.thumbnail, thumbnailImage=p.thumbnail)
			listitem.setInfo('video', p.get_xbmc_list_item())
			# Add the program item to the list
			ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=p.get_url(), listitem=listitem, isFolder=False)

		xbmcplugin.setContent(handle=int(sys.argv[1]), content='episodes')
	except:
		# user cancelled dialog or an error occurred
		print "ERROR: %s (%d) - %s" % ( sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
		ok = False

	return ok
