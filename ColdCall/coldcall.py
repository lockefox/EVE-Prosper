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

query_length = int(conf.get("COLDCALL","query_length"))
query_start = datetime.utcnow() - timedelta(days=query_length)
query_start_str = query_start.strftime("%Y-%m-%d")
full_scrape=1
report=1

corp_length_ceiling = int(conf.get("COLDCALL","corp_length_ceiling"))
character_kills_ceiling = int(conf.get("COLDCALL","character_kills_ceiling"))

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

def load_SQL (queryObj):
	
	progress = 0
	kills_obj = []
	latest_date = ""
	for zkb_return in queryObj:
		print "%s: %s\t%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),latest_date,progress)	
		for kill in zkb_return:
			kills_obj.append(kill)
			
			participants_sql = "INSERT INTO %s (killID,solarSystemID,kill_time,isVictim,shipTypeID,damage,\
				characterID,corporationID,allianceID,factionID,finalBlow,weaponTypeID) " % db_participants
			
			fit_sql = "INSERT INTO %s (killID,characterID,corporationID,allianceID,factionID,shipTypeID,\
				typeID,flag,qtyDropped,qtyDestroyed,singleton) " % db_fits
				
			killID = kill["killID"]
			solarSystemID = kill["solarSystemID"]
			killTime = kill["killTime"]
			
			#Dump victim info first
			victim_info = (
				killID,
				solarSystemID,
				"'%s'" % killTime,
				1,	#isVictim
				kill["victim"]["shipTypeID"],
				kill["victim"]["damageTaken"],
				kill["victim"]["characterID"],
				kill["victim"]["corporationID"],
				kill["victim"]["allianceID"],
				kill["victim"]["factionID"],
				"NULL",	#finalBlow
				"NULL",	#weaponTypeID
				)	#json.dumps(kill["items"]))	#stringify fit for storage (without fit db)
				
			info_str = ','.join(str(item) for item in victim_info)	#join only works on str
			info_str = info_str.rstrip(',')	#strip trailing comma
			victim_participants = "VALUES (%s) ON DUPLICATE KEY UPDATE killID=killID, characterID=characterID" % info_str

			cursor.execute("%s%s" % (participants_sql,victim_participants))
			db.commit()
			
			#Dump killer info
			killers_SQL = "%s VALUES " % participants_sql
			for killer in kill["attackers"]:
				killer_info = (
					killID,
					solarSystemID,
					"'%s'" % killTime,
					0,	#isVictim
					killer["shipTypeID"],
					killer["damageDone"],
					killer["characterID"],
					killer["corporationID"],
					killer["allianceID"],
					killer["factionID"],
					killer["finalBlow"],
					killer["weaponTypeID"],
				)
				
				killer_str = ','.join(str(item) for item in killer_info)
				killer_str = killer_str.rstrip(',')
				killers_SQL = "%s\n (%s)," % (killers_SQL,killer_str)
				
			killers_SQL = killers_SQL.rstrip(',')
			killers_SQL = "%s ON DUPLICATE KEY UPDATE killID=killID, characterID=characterID" % killers_SQL
			
			cursor.execute(killers_SQL)
			db.commit()
			
		#Dump fits
		fits_SQL = "%s VALUES " % fit_sql
		for item in kill["items"]:
			fit_info = (
				killID,
				kill["victim"]["characterID"],
				kill["victim"]["corporationID"],
				kill["victim"]["allianceID"],
				kill["victim"]["factionID"],
				kill["victim"]["shipTypeID"],
				item["typeID"],
				item["flag"],
				item["qtyDropped"],
				item["qtyDestroyed"],
				item["singleton"])
			
			fit_str = ','.join(str(value) for value in fit_info)
			fit_str = fit_str.rstrip(',')
			#fits_SQL = "%s\n (%s)," % (fits_SQL,fit_str)
			
			#would prefer not to have to do it item-by-item, but :update:
			fit_str = "%s (%s) ON DUPLICATE KEY UPDATE killID=killID, characterID=characterID, qtyDropped=qtyDropped + %s, qtyDestroyed = qtyDestroyed + %s"\
				% (fits_SQL,fit_str,item["qtyDropped"],item["qtyDestroyed"])
			
		#fits_SQL = fits_SQL.rstrip(',')
		#fits_SQL = "%s ON DUPLICATE KEY UPDATE killID=killID, characterID=characterID, qtyDropped+=" % fits_SQL
		progress += len(zkb_return)	
		latest_date = killTime
		
	return kills_obj
		
def buildReport(sqlFile = "candidate_US.sql", outFile = "candidates.csv"):
	api = eveapi.EVEAPIConnection()
	
	NPC_corps = []
	query_command = open(sqlFile,'r').read()
	cursor.execute("SELECT corporationID FROM crpnpccorporations")
	for row in cursor.fetchall():
		NPC_corps.append(int(row[0]))
		
	cursor.execute(query_command)
	results = cursor.fetchall()
	
	report_data = []
	report_header = ("characterName",
		"characterID",
		"current corp",
		"kills",
		"losses",
		"latest activity",
		"zkb address",
		"total solo",
		"total kills",
		"total losses",
		"birthday",
		"estimated age (mo)",
		"total age (mo)")
	report_data.append(report_header)
	
	for character_entry in results:
		#report_line = []
		character_id = character_entry[0]
		losses = character_entry[1]
		kills = character_entry[2]
		latest_activity = character_entry[3]
		
		character_info = api.eve.CharacterInfo(characterID=character_id)
		
		character_name = character_info.characterName
		corporation_name = character_info.corporation
		corp_history = character_info.employmentHistory
		
		#parse corp history to estimate character age
		total_age = 0
		estimated_age = 0
		print "%s:%s" % (character_id,datetime.fromtimestamp(character_info.corporationDate))
		earliest_corp_date = datetime.fromtimestamp(character_info.corporationDate)
		previous_corp_date = earliest_corp_date
		for corpinfo in corp_history:
			join_date = datetime.fromtimestamp(corpinfo.startDate)
			corp_id = int(corpinfo.corporationID)
			
			if corp_id in NPC_corps:
				previous_corp_date = join_date
				if join_date < previous_corp_date:
					earliest_corp_date = join_date
				continue
			else:
				delta = previous_corp_date - join_date
				if join_date < previous_corp_date:
					earliest_corp_date = join_date
				previous_corp_date = join_date
				if delta.days > corp_length_ceiling: #6mo corp life?  Assume inactive
					estimated_age+=corp_length_ceiling 
					continue
				estimated_age += delta.days
				
		total_time = datetime.utcnow() - earliest_corp_date
		total_age = round(total_time.days/30)	#months
		estimated_age = round(estimated_age/30) #months
		birthday = earliest_corp_date.strftime("%Y-%m-%d")
		
		#Fetch individual kill stats
		query_length = datetime.utcnow() - timedelta(weeks=52)
		characterQuery = zkb.Query(query_length.strftime("%Y-%m-%d"))
		characterQuery.api_only
		characterQuery.characterID(int(character_id))
		
		total_kills = 0
		total_losses = 0
		for zkbreturn in characterQuery:
			print "%s: fetching kills for %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),character_name)
			for kill in zkbreturn:
				if int(kill["victim"]["characterID"]) == int(character_id):
					total_losses += 1
				else:
					total_kills +=1
			
		characterSoloQuery = zkb.Query(query_length.strftime("%Y-%m-%d"))
		characterSoloQuery.api_only
		characterSoloQuery.characterID(int(character_id))
		characterSoloQuery.solo
		characterSoloQuery.kills
		
		solo_kills = 0
		for zkbsolo in characterSoloQuery:
			solo_kills += len(zkbsolo)
			
		report_line = (
			character_name,
			character_id,
			corporation_name,
			kills,
			losses,
			latest_activity,
			"https://zkillboard.com/character/%s/" % character_id,
			solo_kills,
			total_kills,
			total_losses,
			birthday,
			estimated_age,
			total_age)
		report_data.append(report_line)
	
	result_file = open(outFile,'w')	
	for row in report_data:
		row_str = ','.join(str(item) for item in row)
		result_file.write("%s\n" % row_str)
		
def parseargs():
	global full_scrape,report,query_start_str
	try:
		opts, args = getopt.getopt(sys.argv[1:],"q:h",["scrape_only","report_only","quick"])
	except getopt.GetoptError:
		print "invalid arguments"
		#help()
		sys.exit(2)
		
	for opt,arg in opts:
		if opt == "--scrape_only":		
			report=0
			full_scrape=1
		elif opt == "--report_only":
			report=1
			full_scrape=0
		elif opt == "--quick":		#refreshes DB if out of date, then runs report
			cursor.execute("SELECT DATE(kill_time) FROM %s ORDER BY DATE(kill_time) DESC LIMIT 1" % db_participants)
			query_start_str = cursor.fetchone()[0]

			if str(query_start_str) == str(datetime.utcnow().strftime("%Y-%m-%d")):
				full_scrape = 0
				print "DB up to date, skipping scrape"
			else:
				full_scrape = 1
			report = 1
			
def main():
	db_init()
	parseargs()

	if full_scrape == 1:

		query_AR = zkb.Query(query_start_str)
		query_AR.factionID(500004)	#gallente Faction
		query_AR.api_only
		query_AR.beforeKillID(zkb.fetchLatestKillID(query_start_str))	#preload latest killID
		
		print "Fetching data from %s" % query_AR
		kills_obj = load_SQL(query_AR)
	
		dumpfile = open("dump_coldcall.json",'w')
		dumpfile.write(json.dumps(kills_obj,indent=4))
	
	if report == 1:
		buildReport()
	
if __name__ == "__main__":
	main()