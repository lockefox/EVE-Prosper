#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import ElementTree
import MySQLdb
import ConfigParser

########## INIT VARS ##########
BPO_file = open("jeves.blueprints.xml")
lookup_json = open("lookup.json")
lookup = json.load(lookup_json)
crash_file = "material_bridge_crash.json"
crash_obj={}
BPOs = ElementTree.parse(BPO_file)

#Config File Globals
conf = ConfigParser.ConfigParser()
conf.read(["bridge.ini", "bridge_local.ini"])

########## GLOBALS ##########
regionlist = None	#comma separated list of regions (for EMD history)
systemlist = None	#comma separated list of systems (for EC history)
itemlist = None		#comma separated list of items (default to full list)
csv_only = int(conf.get("GLOBALS","csv_only"))				#output CSV instead of SQL
sql_init_only = int(conf.get("GLOBALS","sql_init_only"))	#output CSV CREATE file


########## DB VARS ##########
db_table = conf.get("MATERIALDESTROYED","db_table")
db_name = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))
db_cursor = None
db = None

kill_db_name = conf.get("GLOBALS","db_name")
kill_db_table = conf.get("GLOBALS","emd_table")
kill_db_IP = conf.get("GLOBALS","db_host")
kill_db_user = conf.get("GLOBALS","db_user")
kill_db_pw = conf.get("GLOBALS","db_pw")
kill_db_port = int(conf.get("GLOBALS","db_port"))
kill_db_cursor = None
kill_db = None

def init:
	global db_cursor, db
	global kill_db_cursor, kill_db
	
	#Two cursors to allow for disperate hosting (though I can't imagine why)
	try:
		kill_db = MySQLdb.connect(host=kill_db_IP, user=kill_db_user, passwd=kill_db_pw, port=kill_db_port, db=kill_db_name)	
		kill_db_cursor = kill_db.cursor()	
	except MySQLdb.Error as er:
		print "Cannot connect to kill database"
		sys.exit(2)

	#check if kill data table exists
	try:
		kill_db_cursor.execute("SELECT 1 FROM %s LIMIT 1" % kill_db_table)
	except MySQLdb.OperationalError as e:
		print "%s does not exist.  Initialize with zkb_scraper" % kill_db_table
		sys.exit(2)
	except MySQLdb.ProgrammingError as er:
		print "%s does not exist.  Initialize with zkb_scraper" % kill_db_table
		sys.exit(2)
	print "Kill DB Connection:\t\tGOOD"

	try:
		db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_name)	
		db_cursor = db.cursor()
	except MySQLdb.Error as er:
		print "Cannot connect to kill database"
		sys.exit(2)
		
	try:
		db_cursor.execute("CREATE TABLE %s (\
			`date` date NOT NULL,\
			`week` varchar(8) NOT NULL,\
			`typeID` int(8) NOT NULL,\
			`typeGroup` int(8) NOT NULL,\
			`systemID` int(8) NOT NULL,\
			`destroyed` bigint(32) DEFAULT 0,\
			PRIMARY KEY (`date`,`typeID`,`systemID`))\
			ENGINE=InnoDB DEFAULT CHARSET=latin1" % db_name)
	except MySQLdb.OperationalError as e:
		if (e[0] == 1050): #Table Already Exists
			print "%s table already created" % db_name
		else:
			raise e		
			sys.exit(2)
	print "Material DB connection:\t\tGOOD"
	
	