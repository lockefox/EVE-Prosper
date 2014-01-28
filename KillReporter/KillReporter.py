#!/Python27/python.exe

import sys, gzip, StringIO, sys, math, os, getopt, time, json, socket
import urllib2
import MySQLdb
import ConfigParser
from datetime import datetime, timedelta

from eveapi import eveapi
import zkb

conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

cursor = None
db = None

db_schema = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))

db_participants = conf.get("KILL_REPORTER","db_participants")
db_fits = conf.get("KILL_REPORTER","db_fits")

#query_length = int(conf.get("COLDCALL","query_length"))
#query_start = datetime.utcnow() - timedelta(days=query_length)
#query_start_str = query_start.strftime("%Y-%m-%d")

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
		
def load_SQL(queryObj):
	progress = 0
	kills_obj = []
	latest_date = ""
	for zkb_return in queryObj:
		print "%s: %s\t%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),latest_date,progress)	
		for kill in zkb_return:
			kills_obj.append(kill)
			participants_cols = (
				"killID",
				"solarSystemID",
				"kill_time",
				"isVictim",
				"shipTypeID",
				"damage",
				"characterID",
				"characterName",
				"corporationID",
				"corporationName",
				"allianceID",
				"allianceName",
				"factionID",
				"factionName",
				"finalBlow",
				"weaponTypeID",
				"points",
				"totalValue")
				
			participants_sql = "INSERT INTO %s (%s) " % (db_participants,','.join(participants_cols))
			
			fit_sql = "INSERT INTO %s (killID,characterID,corporationID,allianceID,factionID,shipTypeID,\
				typeID,flag,qtyDropped,qtyDestroyed,singleton) " % db_fits
				
			killID = kill["killID"]
			solarSystemID = kill["solarSystemID"]
			killTime = kill["killTime"]
			
			victim_name = kill["victim"]["characterName"]
			victim_corp = kill["victim"]["corporationName"]
			victim_alliance = kill["victim"]["allianceName"]
			try:
				victim_faction = kill["victim"]["factionName"]
			except KeyError:
				victim_faction = "NULL"
				
			victim_name.replace('\'','\\\'')	#replace (') to avoid SQL errors
			victim_corp.replace('\'','\\\'')
			victim_alliance.replace('\'','\\\'')
			victim_faction.replace('\'','\\\'')
			
			try:
				points = kill["zkb"]["points"]
				totalValue = kill["zkb"]["totalValue"]
			except KeyError:
				points = "NULL"
				totalValue = "NULL"
			victim_info = (
				killID,
				solarSystemID,
				"'%s'" % killTime,
				1,	#isVictim
				kill["victim"]["shipTypeID"],
				kill["victim"]["damageTaken"],
				kill["victim"]["characterID"],
				victim_name,
				kill["victim"]["corporationID"],
				victim_corp,
				kill["victim"]["allianceID"],
				victim_alliance,
				kill["victim"]["factionID"],
				victim_faction,
				"NULL",	#finalBlow
				"NULL",	#weaponTypeID
				points,
				totalValue
				)	#json.dumps(kill["items"]))	#stringify fit for storage (without fit db)
				
			info_str = ','.join(str(item) for item in victim_info)	#join only works on str
			info_str = info_str.rstrip(',')	#strip trailing comma
			victim_participants = "VALUES (%s) ON DUPLICATE KEY UPDATE killID=killID, characterID=characterID" % info_str

			cursor.execute("%s%s" % (participants_sql,victim_participants))
			db.commit()
def main():
	db_init()
	
	#build query
	latestKillID = zkb.fetchLatestKillID("2014-01-26")
	BR5R_Query = Query("2014-01-26")
	BR5R_Query.api_only
	BR5R_Query.systemID(30002157)
	BR5R_Query.losses
	BR5R_Query.beforeKillID(latestKillID)
	
	print "Fetching: %s" % BR5R_Query
	kills_obj = load_SQL(BR5R_Query)
	

if __name__ == "__main__":
	main()