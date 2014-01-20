#!/Python27/python.exe

import sys, gzip, StringIO, sys, math, os, getopt, time, json, socket
import urllib2
import MySQLdb
import ConfigParser
from datetime import datetime, timedelta

from eveapi import eveapi
import zkb

#import webapp2
#from google.appengine.ext import ndb
##need appengine SDK: https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python
conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

cursor = None
db = None

db_schema = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))

db_participants = conf.get("COLDCALL","db_participants")
db_fits = conf.get("COLDCALL","db_fits")

def db_init():
	global cursor,db
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
	cursor = db.cursor()
	print "DB connection:\tGOOD"
	#Check for existing tables
	cursor.execute("SHOW TABLES LIKE '%s'" % db_participants)
	#db.commit()
	participant_db_exists = len(cursor.fetchall())	#zero if not initialized
	
	if participant_db_exists == 0:
		create_db = open("%s.sql" % db_participants, 'r').read()
		try:
			cursor.execute(create_db)
			db.commit()
		except Exception, e:
			print e
			sys.exit(2)
		print "%s.%s table:\tCREATED" % (db_schema,db_participants)
	else:
		print "%s.%s table:\tGOOD" % (db_schema,db_participants)
		
	cursor.execute("SHOW TABLES LIKE '%s'" % db_fits)
	#db.commit()
	fit_db_exists = len(cursor.fetchall())	#zero if not initialized
	
	if fit_db_exists == 0:
		create_db = open("%s.sql" % db_fits, 'r').read()
		try:
			cursor.execute(create_db)
			db.commit()
		except Exception, e:
			print e
			sys.exit(2)
		print "%s.%s table:\tCREATED" % (db_schema,db_fits)
	else:
		print "%s.%s table:\t\tGOOD" % (db_schema,db_fits)
	
def main():
	db_init()
	
	query_length = int(conf.get("COLDCALL","query_length"))
	query_start = datetime.utcnow() - timedelta(days=query_length)
	query_start_str = query_start.strftime("%Y-%m-%d")

	query_AR = zkb.Query(query_start_str)
	query_AR.factionID(500004)	#gallente Faction
	query_AR.api_only
	query_AR.beforeKillID(zkb.fetchLatestKillID(query_start_str))
	
	print query_AR
	for zkb_return in query_AR:
		print len(zkb_return)
		for kill in zkb_return:
			participants_sql = "INSERT INTO %s (killID,solarSystemID,kill_time,isVictim,shipTypeID,damage,\
				characterID,corporationID,allianceID,factionID,finalBlow,weaponTypeID,fit_json)" % db_participants
			
			fit_sql = "INSERT INTO %s (killID,characterID,corporationID,allianceID,factionID,shipTypeID,\
				typeID,flag,qtyDropped,qtyDestroyed,singleton)" % db_fits
			
			
			
	dumpfile = open("dump_coldcall.json",'w')
	dumpfile.write(json.dumps(kills_obj,indent=4))
	
if __name__ == "__main__":
	main()