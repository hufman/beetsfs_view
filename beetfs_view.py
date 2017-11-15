#!/usr/bin/env python3

"""
This program presents a FUSE virtual filesystem based on the contents
of a Beets database file.
"""

import argparse
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from beetfs import beetsdb, fs

def parse_args(args=None):
	parser = argparse.ArgumentParser()
	parser.add_argument('mountpoint',
	                    help='Location to mount the FS')
	parser.add_argument('--realroot', required=True,
	                    help='Location to load files from')
	parser.add_argument('--dbpath', required=True,
	                    help='Location of Beets DB')
	parsed_args = parser.parse_args(args)
	return parsed_args
	
if __name__ == '__main__':
	args = parse_args()
	db = beetsdb.BeetsDB(args.dbpath)
	fs.run(args.mountpoint, args.realroot, db)
