#!/Python27/python.exe

#####	DB_BUILDER.PY	#####
#	A wrapper to build the Prosper DB's locally for the purpose of debug
#
#	Coalesses the various DB building tools into one easy script
#	Controlled by "config.ini" file + some limited cmd line args
#
#############################

#####		INITS		#####
import sys,csv, sys, math, os, gzip, getopt, subprocess, math
import ConfigParser
import urllib2
import MySQLdb
#####		GLOBALS		#####
config_file = "config.ini"

def proginit():
	#Tests outgoing connections for proper functioning.  Will abort program if any fail
	
	#Load config file
	config = ConfigParser.ConfigParser()
	config.read(config_file)
	
	#Verify internet connections#
	
	try:	#eve-central
		urllib2.urlopen(urllib2.Request(config.get("EVE_CENTRAL","central_path")))
	except URLERROR as e:
		print "Unable to query EVE-Central Dump repository at %s" % config.get("EVE_CENTRAL","central_path")
		print e.reason
		sys.exit(4)
		
	try:	#zkillboard
		urllib2.urlopen(urllib2.Request(config.get("TOASTER_CFG","toaster_path")))
	except URLERROR as e:
		print "Unable to query Killboard repository at %s" % config.get("TOASTER_CFG","toaster_path")
		print e.reason
		sys.exit(4)
		
	#Verify DB connection
	
	try:
		con = MySQLdb.connect(host=config.get("GLOBALS","db_IP"), user=config.get("GLOBALS","db_username"), passwd=config.get("GLOBALS","db_pw"), port=int(config.get("GLOBALS","db_port")), db=config.get("GLOBALS","eve_marketdata"))
		cur = con.cursor()
		cur.execute("SELECT VERSION()")
		data = cur.fetchone()
		print "DB Version: %s" % data
	except MySQLdb.Error, e:
		print "Unable to connect to destination database"
		print "ERROR %d: %s" % (e.args[0],e.args[1])
		sys.exit(5)
		
	con.close()
	
