#!/Python27/python.exe

import sys,csv, sys, math, os, gzip, getopt, subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue

config_file = "config.ini"
config = ConfigParser.ConfigParser()
config.read(config_file)

startdate=datetime.datetime.strptime(config.get("GLOBALS","startdate"),"%Y-%m-%d")
enddate=(datetime.datetime.now())
debug=config.get("DEBUG","debug")

def proginit():
	try: #kb-site
		urllib2.urlopen(urllib2.Request(config.get("TOASTER_CFG","toaster_path")))
	except urllib2.URLError as e:
		print "Unable to query %s" % config.get("TOASTER_CFG","toaster_path")
		print e.code
		sys.exit(4)	
		
	