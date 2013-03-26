#!/Python27/python.exe

import sys,csv, sys, math, os, gzip, getopt, subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue

#Config File Globals
config_file = "config.ini"
config = ConfigParser.ConfigParser()
config.read(config_file)

startdate=datetime.datetime.strptime(config.get("GLOBALS","startdate"),"%Y-%m-%d")
enddate=(datetime.datetime.now())
debug=config.get("DEBUG","debug")

#Thread Globals
queue = Queue.Queue()

#DB Globals
cursor=None
class strikes:
	def __init__(self, what):
		self.strike = 0
		self.max_strikes = config.get("GLOBALS","strikes")
		self.what = what
	def increment(self):
		self.strike +=1
		self.strike_out()
	def strike_out(self):
		if self.strike > self.max_strikes:
			print "Exceded retry fail limit for %s" % self.what
			sys.exit(2)
			
def proginit():
	#Tests outgoing connections for proper functioning.  Will abort program if any fail
	
	#Load config file

	
	#Verify internet connections#
	try:	#eve-central
		urllib2.urlopen(urllib2.Request(config.get("EVE_CENTRAL","central_path")))
	except urllib2.URLError as e:
		print "Unable to query EVE-Central Dump repository at %s" % config.get("EVE_CENTRAL","central_path")
		print e.code
		sys.exit(4)
	except urllib2.HTTPError as er:
		print "Unable to query EVE-Central Dump repository at %s" % config.get("EVE_CENTRAL","central_path")
		print er.code
		sys.exit(4)
		
	try:	#zkillboard
		urllib2.urlopen(urllib2.Request(config.get("TOASTER_CFG","toaster_path")))
	except urllib2.URLError as e:
		print "Unable to query Killboard repository at %s" % config.get("TOASTER_CFG","toaster_path")
		print e.code
		sys.exit(4)
	except urllib2.HTTPError as er:
		print "Unable to query Killboard repository at %s" % config.get("TOASTER_CFG","toaster_path")
		print er.code
		sys.exit(4)
	#Verify DB connection
	try:
		con = MySQLdb.connect(host=config.get("GLOBALS","db_IP"), user=config.get("GLOBALS","db_username"), passwd=config.get("GLOBALS","db_pw"), port=int(config.get("GLOBALS","db_port")), db=config.get("GLOBALS","root_dbname"))
		cur = con.cursor()
		cur.execute("SELECT VERSION()")
		data = cur.fetchone()
		print "DB Version: %s" % data
	except MySQLdb.Error, e:
		print "Unable to connect to destination database"
		print "ERROR %d: %s" % (e.args[0],e.args[1])
		sys.exit(5)
	
	print "Validated connections"
	con.close()

def parseargs():
	global filepath,outputpath
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hs:ed:",["startdate=","enddate=","debug"])
	except getopt.GetoptError:
		print 'DB_Builder.py -s YYYY-MM-DD'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			help()
		elif opt in ("-s", "--startdate"):
			try:
				datetime.strptime(arg, "%Y-%m-%d")
			except ValueError:
				print "Invalid startdate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
				
			startdate=datetime.strptime(arg,"%Y-%m-%d")
		elif opt in ("-e", "--enddate"):
			try:
				datetime.strptime(arg, "%Y-%m-%d")
			except ValueError:
				print "Invalid enddate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
			
			enddate=datetime.strptime(arg,"%Y-%m-%d")
		
		elif opt in ("-d","--debug"):
			debug=1
		else:
			help()
	print "parsed input arguments"
		
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
	db = MySQLdb.connect(host=config.get("GLOBALS","db_IP"), user=config.get("GLOBALS","db_username"), passwd=config.get("GLOBALS","db_pw"), port=int(config.get("GLOBALS","db_port")), db=config.get("GLOBALS","root_dbname"))
	global cursor
	cursor = db.cursor()
	
	#create tables in database
		#raw-price db (DEBUG ONLY)
	cursor.execute ("CREATE TABLE IF NOT EXISTS `%s`\
		(itemID INTEGER NOT NULL, \
		order_date date NOT NULL, \
		regionID INTEGER NOT NULL, \
		systemID INTEGER NOT NULL, \
		order_type VARCHAR(20) NOT NULL, \
		price_max DECIMAL(12,2) NULL, \
		price_min DECIMAL (12,2) NULL, \
		price_avg DECIMAL (12,2) NULL, \
		price_stdev DECIMAL (8,4) NULL, \
		other DECIMAL (12,2) NULL, \
		PRIMARY KEY (order_date))" % config.get("EVE_CENTRAL","raw_db"))
		#processing SQL for daily dump data (DEBUG ONLY.  Should be empty after proc)
	#cursor.execute ("CREATE TABLE IF NOT EXISTS `%s`\
	#	(orderID INTEGER NOT NULL, \
	#	order_date date NOT NULL, \
	#	regionid, INTEGER NOT NULL, \
	#	systemid, INTEGER NOT NULL, \
	#	typeid, INTEGER NOT NULL, \
	#	order_type INTEGER NOT NULL, \
	#	price DECIMAL(12,2) NULL, \
	#	volenter INTEGER NOT NULL, \
	#	PRIMARY KEY (order_date))" % config.get("EVE_CENTRAL","dumpproc_db"))
		#processed data (in PROSPER)
	cursor.execute("CREATE TABLE IF NOT EXISTS %s\
		(itemID INTEGER NOT NULL, \
		order_date date NOT NULL, \
		regionID INTEGER NOT NULL, \
		systemID INTEGER NOT NULL, \
		order_type VARCHAR(20) NOT NULL, \
		price_max DECIMAL(12,2) NOT NULL, \
		price_min DECIMAL (12,2) NOT NULL, \
		price_avg DECIMAL (12,2) NOT NULL, \
		price_stdev DECIMAL (8,4) NOT NULL, \
		other DECIMAL (12,2) NULL, \
		PRIMARY KEY (order_date) \
		)" % config.get("EVE_CENTRAL","prosper_db"))
		
		#kill-data database (in PROSPER)
	cursor.execute("CREATE TABLE IF NOT EXISTS %s\
		(itemID INTEGER NOT NULL, \
		kill_date date NOT NULL, \
		destroyed_global INTEGER NOT NULL, \
		destroyed_highsec INTEGER NOT NULL, \
		destroyed_nullsec INTEGER NOT NULL, \
		destroyed_wspace INTEGER NOT NULL, \
		est_value DECIMAL (12,2) NOT NULL, \
		PRIMARY KEY (kill_date)\
		)" % config.get("TOASTER_CFG","kill_db"))
		
		#builder database (in PROSPER)
	cursor.execute("CREATE TABLE IF NOT EXISTS %s\
		(itemID INTEGER NOT NULL, \
		order_date date NOT NULL, \
		item_price DECIMAL(12,2) NOT NULL, \
		build_now DECIMAL(12,2) NOT NULL, \
		build_7d DECIMAL(12,2) NOT NULL, \
		build_14d DECIMAL(12,2) NOT NULL, \
		build_30d DECIMAL(12,2) NOT NULL, \
		PRIMARY KEY (order_date)\
		)" % config.get("BUILDER_CFG","builder_db"))
		
	print "Database tables configured"