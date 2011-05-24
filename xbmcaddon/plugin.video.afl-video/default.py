"""
	Plugin for streaming content from AFL.com.au
"""
import sys

from resources.lib import utils, index, matches, match, teams, videos

# plugin constants
__plugin__  = "AFL Video"
__author__  = "Andy Botting"
__url__     = ""
__svn_url__ = ""
__version__ = "0.1.0"
__credits__ = "AFL, Team XBMC"

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__" :
	params_str = sys.argv[2]
	params = utils.get_url(params_str)

	if (len(params) == 0):
		# List index
		index.make_list()
	else:
		# Picked a type
		if params.has_key('type'):
			if params['type'] == 'matches':
				# List matches
				matches.make_list()

			elif params['type'] == 'teams':
				# List teams
				teams.make_list()

			else:
				# List videos for categories
				videos.make_list(params_str)

		# Fallback to showing video items
		else:
			videos.make_list(params_str)
