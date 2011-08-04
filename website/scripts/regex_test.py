#!/usr/bin/env python

import re

strings = ['Rnd01', 'Rnd1', 'Rd1', 'Rd01', 'RD1', 'RD01', 'Rnd 01', 'Round 01', 'Round 1', 'fw01', 'FW1', 'Round blah', 'Rnz01', 'Rd201']

for string in strings:
	match = re.search(r"ro?u?n?d\s?(\d{1,2})", string, flags=re.IGNORECASE)
	if match:
		print "Match for %s: %s" % (string, match.groups())
	else:
		print "No match for %s" % string
