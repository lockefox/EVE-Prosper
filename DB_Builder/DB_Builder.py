#!/Python27/python.exe

#####	DB_BUILDER.PY	#####
#	A wrapper to build the Prosper DB's locally for the purpose of debug
#
#	Coalesses the various DB building tools into one easy script
#	Controlled by "config.ini" file + some limited cmd line args
#
#############################

#####		INITS		#####
import sys,csv, sys, math, os, gzip, getopt, subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue
#####		GLOBALS		#####
config_file = "config.ini"
config = ConfigParser.ConfigParser()
config.read(config_file)

startdate=datetime.strptime(config.get("GLOBALS","startdate"),"%Y-%m-%d")
enddate=(datetime.datetime.now()).strftime("%Y-%m-%d")
debug=config.get("DEBUG","debug")

queue = Queue.Queue()

def proginit():
	#Tests outgoing connections for proper functioning.  Will abort program if any fail
	
	#Load config file

	
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

def parseargs():
	global filepath,outputpath
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hs:ed:",["startdate=","enddate=","debug"])
	except getopt.GetoptError:
		print 'log2ppd.py -i <filepath>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			help()
		elif opt in ("-s", "--startdate"):
			try:
				time.strptime(arg, "%Y-%m-%d")
			except ValueError:
				print "Invalid startdate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
				
			startdate=datetime.strptime(arg,"%Y-%m-%d")
		elif opt in ("-e", "--enddate"):
			try:
				time.strptime(arg, "%Y-%m-%d")
			except ValueError:
				print "Invalid enddate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
			
			enddate=datetime.strptime(arg,"%Y-%m-%d")
		
		elif opt in ("-d","--debug"):
			debug=1
		else:
			help()

		
def help():
	print """DB_Builder.py
		Used to create/maintain local DB to mirror the one Prosper hosts in Appengine
		this is to minimize debug on costly server time inside appengine
	
	OPTIONS:
		--startdate: YYYY-MM-DD	default=Crucible release (2011-11-29)
		(--enddate: YYYY-MM-DD)	default=today
		(--debug)				default=false
	"""
	sys.exit(1)
	
def dbinit():
	db = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, port=int(DATABASE_PORT), db=DATABASE_NAME)
	cursor = db.cursor()
	return cursor

def main():
	
if __name__ == "__main__":
	proginit()
	parseargs()
	cursor = dbinit()
	main()