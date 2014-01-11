#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

systemlist="toaster_systemlist.json"	#system breakdown for destruction binning
lookup_file="lookup.json"				#ID->name conversion list
shiplist="toaster_shiplist.json"		#Allows stepping by groupID
crash_file="zkb_scraper_crash.json"		#tracks crashes for recovering gracefully
log_file = "zkb_scraper_log.txt"		#Logs useful run data.  Moves old verson?
zkb_base="https://zkillboard.com/"
lookup_json = open(lookup_file)
system_json = open(systemlist)
ships_json = open(shiplist)
lookup = json.load(lookup_json)
systems= json.load(system_json)
ship_list=json.load(ships_json)
headder_err=0
please_force=0

#Config File Globals
conf = ConfigParser.ConfigParser()
conf.read(["scraper.ini", "scraper_local.ini"])

########## GLOBALS ##########

csv_only=conf.get("GLOBALS", "csv_only")							#output CSV instead of SQL
sql_init_only=conf.get("GLOBALS", "sql_init_only")					#output CSV CREATE file
sql_file="pricedata.sql"
zkb_default_args=conf.get("ZKB","default_args")
start_date=conf.get("ZKB", "startdate")
start_date_test=time.strptime(start_date,"%Y-%m-%d")
db_name=""
db_schema=""
db=None
db_cursor=None
User_Agent = "lockefox"
crash_obj={}
call_sleep_default=float(conf.get("ZKB", "default_sleep"))
call_sleep = call_sleep_default
log_filehandle = open(log_file, 'a+')

zkb_query_str = conf.get("ZKB","default_args")

corporations = {} #corporations[id]={kills:##,losses:##,members:[id,id,]}
alliances = {}
characters = {}

faction_filter = 0
chracter_filter = 0
shiptype_filter = 0

def init():
	
	try:	#EVE-Marketdata.com connection
		request = urllib2.Request(zkb_base)
		request.add_header('Accept-Encoding','gzip')
		request.add_header('User-Agent',User_Agent)	#Don't forget request headders
		urllib2.urlopen(request)
	except urllib2.URLError as e:
		print "Unable to connect to zKB at %s" % zkb_base
		print e.code
		print e.headers
		sys.exit(4)
	except urllib2.HTTPError as er:
		print "Unable to connect to zKB at %s" % zkb_base
		print er.code
		print er.headers
		sys.exit(4)
	print "zKillboard connection:\tGOOD"
	#time.sleep(10)
	
def parseargs():
	global zkb_query_str
	global faction_filter, character_filter, shiptype_filter
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],"rh:s:",["system=","region=","faction=","csv","items=","startdate=","groups=","character=","shiptype=","please"])
	except getopt.GetoptError,e:
		print "invalid arguments"
		print e
		#help()
		sys.exit(2)
		
	for opt, arg in opts:
		if opt == "-h":
			print "herp"
		elif opt == "--csv":
			global csv_only
			csv_only=1
			print "CSV function not supported yet"
		elif opt == "--startdate":
			global start_date,start_date_test
			start_date=arg
			try:	#Validate input
				time.strptime(start_date,"%Y-%m-%d")
			except ValueError as e:
				print e
				print "Valid date format: YYYY-mm-dd"
				sys.exit(2)
			start_date_test=time.strptime(start_date,"%Y-%m-%d")
		elif opt == "--region":
			zkb_query_str = "%sregionID/%s/" % (zkb_query_str,arg)
			
		elif opt == "--system":
			zkb_query_str = "%ssystemID/%s/" % (zkb_query_str,arg)
			
		elif opt == "--faction":
			zkb_query_str = "%sfactionID/%s/" % (zkb_query_str,arg)
			faction_filter = arg
		
		elif opt == "--character":
			zkb_query_str = "%scharacterID/%s/" % (zkb_query_str,arg)
			character_filter = arg
		elif opt == "--groups":
			zkb_query_str = "groupID/%s/" % (zkb_query_str,arg)
		elif opt == "--shiptype":
			shiptype_filter = arg
		elif opt == "--please":
			print "WARNING: --please can cause zkb bans.  Ignoring throtling info"
			time.sleep(5)
			global please_force
			please_force=1
		else:
			print "herp"

def feed_primer():	#initial fetch to initilaize crawler
	global start_killID
	global call_sleep
	zkb_primer_args = "losses/solo/limit/1/"
	zkb_addr = "%sapi/%s%s" % (zkb_base,zkb_default_args,zkb_primer_args)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	
	headers=[]
	log_filehandle.write("%s:\tQuerying %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), zkb_addr))
	for tries in range (0,5):
		time.sleep(call_sleep_default*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
		except urllib2.HTTPError as e:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), er))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	if please_force==0:
		snooze_setter(header_hold)
	else:
		time.sleep(1)
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	
	try:
		start_killID = JSON_obj[0]["killID"]	#"latest kill" in zKB
	except TypeError as e:
		print "zKB API looks to be down"
		print JSON_obj
		print headers
		sys.exit(4)
	return start_killID

def kill_crawler(start_killID,group,groupName,progress):
	global crash_obj
	
	parsed_kills = [progress,start_killID,0,None]
	
	zkb_primer_args = "losses/groupID/%s/" % group
	zkb_addr = "%sapi/beforeKillID/%s/%s%s" % (zkb_base,start_killID,zkb_default_args,zkb_primer_args)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	headers=[]
	log_filehandle.write("%s:\tQuerying %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), zkb_addr))
	for tries in range (0,5):
		time.sleep(call_sleep_default*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
			raw_zip = opener.open(request)
			dump_zip_stream = raw_zip.read()
		except urllib2.HTTPError as e:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), er))
			print "URLError.  Retry %s: %s" %(zkb_addr,tries+1)
			continue
		except socket.error as err:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err))
			print "Socket Error.  Retry %s: %s" %(zkb_addr,tries+1)
			
		try:
			dump_IOstream = StringIO.StringIO(dump_zip_stream)
			zipper = gzip.GzipFile(fileobj=dump_IOstream)
			JSON_obj = json.load(zipper)
		except ValueError as errr:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), errr))
			print "Empty response.  Retry %s: %s" %(zkb_addr,tries+1)
			
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	
	if please_force==0:
		snooze_setter(header_hold)
	else:
		time.sleep(1)
	
	
	#zipper = gzip.GzipFile(fileobj=dump_IOstream)
	#
	#JSON_obj = json.load(zipper)


	if len(JSON_obj)==0:
		parsed_kills[2]=1
	next_killID=start_killID
	earliest_killID=[time.gmtime(),next_killID]
	for kill in JSON_obj:
		#parsed_kills[1]=kill["killID"]
		ship_destroyed = kill["victim"]["shipTypeID"]
		system = kill["solarSystemID"]
		date_killed = time.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		date_str = time.strftime("%Y-%m-%d",date_killed)
		
		#checks chronological order of kills returned.  Set parsed_kills[1] to earliest kill in set
		if date_killed < earliest_killID[0]:
			earliest_killID=[date_killed,kill["killID"]]
			parsed_kills[1]=kill["killID"]
		
		if date_killed<start_date_test:		#Only process to desired date
			parsed_kills[2]=1
			break
		
		try:
			item_name=lookup["all_types"][str(ship_destroyed)]
		except KeyError as e:
			item_name=str(ship_destroyed)
			

		
		value_str = "'%s','%s',%s,%s,%s,%s" % (date_str,time.strftime("%Y-%U",date_killed),ship_destroyed,lookup["groups"][str(ship_destroyed)],system,1)
		db_cursor.execute("INSERT INTO %s (date,week,typeID,typeGroup,systemID,destroyed) VALUES (%s) ON DUPLICATE KEY UPDATE destroyed = destroyed + 1" % (db_name,value_str))
		db.commit()
		
		cargo_report={}
		for cargo_items in kill["items"]:
			if cargo_items["qtyDestroyed"]>0:
				if cargo_items[str("typeID")] in cargo_report:	#Duplicate destroyed item
					cargo_report[str(cargo_items[str("typeID")])]+=cargo_items["qtyDestroyed"]
				else:											#New destroyed item
					cargo_report[str(cargo_items[str("typeID")])]=cargo_items["qtyDestroyed"]
		
		for key,value in cargo_report.iteritems():
			try:
				key_group = lookup["groups"][str(key)]
			except KeyError as e:
				key_group = 0
			value_str = "'%s','%s',%s,%s,%s,%s" % (date_str,time.strftime("%Y-%U",date_killed),key,key_group,system,value)
			db_cursor.execute("INSERT INTO %s (date,week,typeID,typeGroup,systemID,destroyed) VALUES (%s) ON DUPLICATE KEY UPDATE destroyed = destroyed + %s" % (db_name,value_str,value))
			db.commit()


		parsed_kills[0]+=1
		log_filehandle.write("%s:\t%s killID %s:%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),item_name,kill["killID"],date_str))
		crash_obj["parsed_data"][group]=parsed_kills[1]
		crash_obj["progress"][group]=parsed_kills[0]
		crash_handler(crash_obj)
		#print "-------"
	parsed_kills[3]=date_str
	return parsed_kills
	
def crash_recover():
	global crash_obj
	tidy_reset=0
	try:
		with open(crash_file):
			print "recovering from %s" % crash_file
			crash_json=open(crash_file)
			crash_progress=json.load(crash_json)
			tidy_reset=1
			pass
	except IOError:	
		print "no crash log found.  Executing as normal"
		
		pass
	
	if tidy_reset:
		print "\tRestoring progress"
		crash_json = open(crash_file)
		crash_obj=json.load(crash_json)
	else:
		validate_delete = raw_input("Delete all entries to %s in %s.%s?  (Y/N)" % (start_date,db_schema,db_name))
		if validate_delete.upper() == 'Y':
			db_cursor.execute("DELETE FROM %s WHERE date>='%s'" % (db_name,start_date))
			db.commit()
			print "\tCleaning up ALL entries to %s" % start_date
		else:
			print "\tWARNING: values may be wrong without scrubbing duplicates"
			#Initialize crash_obj
		crash_obj={}
		crash_obj["parsed_data"]={}
		crash_obj["progress"]={}

def snooze_setter(header):
	global call_sleep, headder_err
	try:	#see if default sleep timer is defined
		conn_sleep_time= int(header["X-Bin-Seconds-Between-Request"])
	except KeyError as e:
		if headder_err==0:
			print "WARNING: %s not found" %e
			print header
			headder_err+=1
		call_sleep=call_sleep_default
		return	#return if default case
		
	try:	#see if allowances are defined
		conn_allowance = int(header["X-Bin-Attempts-Allowed"])
		conn_reqs_used = int(header["X-Bin-Requests"])		
	except KeyError as e:
		if headder_err==0:
			print "WARNING: %s not found" %e
			print header
			headder_err+=1
		call_sleep=conn_sleep_time
		return	#return if default case
		
	if (conn_reqs_used+1)==conn_allowance:
		call_sleep = conn_sleep_time #full back-off if allowance is out
	##### Polite Scheme.  Need to speed/fail test
	#elif conn_reqs_used > 1:
	#	call_sleep = (conn_sleep_time/conn_allowance)*conn_reqs_used #slow down if using up some budget
	#############################################
	else:
		call_sleep = 0 #conn_sleep_time/5		#Go as fast as possible
	##print "X-Bin-Attempts-Allowed: %s" % conn_allowance
	##print "X-Bin-Requests: %s" % conn_reqs_used
	##print "X-Bin-Seconds-Between-Request: %s" % conn_sleep_time
def kill_crawler2(start_killID,queryStr,progress):
	global corporations,alliances,characters
	global crash_obj
	
	zkb_addr = "%sapi/beforeKillID/%s/%s" % (zkb_base,start_killID,queryStr)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	headers=[]
	log_filehandle.write("%s:\tQuerying %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), zkb_addr))
	for tries in range (0,5):
		time.sleep(call_sleep_default*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
			raw_zip = opener.open(request)
			dump_zip_stream = raw_zip.read()
		except urllib2.HTTPError as e:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), er))
			print "URLError.  Retry %s: %s" %(zkb_addr,tries+1)
			continue
		except socket.error as err:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err))
			print "Socket Error.  Retry %s: %s" %(zkb_addr,tries+1)
			
		try:
			dump_IOstream = StringIO.StringIO(dump_zip_stream)
			zipper = gzip.GzipFile(fileobj=dump_IOstream)
			JSON_obj = json.load(zipper)
		except ValueError as errr:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), errr))
			print "Empty response.  Retry %s: %s" %(zkb_addr,tries+1)
			
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	
	if please_force==0:
		snooze_setter(header_hold)
	else:
		time.sleep(1)
	
	if len(JSON_obj)==0:
		progress["complete"] = 1
		
	next_killID=start_killID
	earliest_killID=[time.gmtime(),next_killID]
	
	for kill in JSON_obj:
		date_killed = time.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")

		
		if date_killed < earliest_killID[0]:
			earliest_killID=[date_killed,kill["killID"]]
			progress["killID"]=kill["killID"]
			progress["earlyDate"] = kill["killTime"]
			
		if date_killed<start_date_test:		#Only process to desired date
			progress["complete"] = 1
			break
		

		if 	faction_filter:
			faction_list = faction_filter.split(',')
			faction_list.astype(int)
			if int(kill["victim"]["factionID"]) == int(faction_filter):
				kill_data_dump(kill)
				progress["kills_parsed"] += 1
			elif int(kill["victim"]["factionID"]) in faction_list:
				kill_data_dump(kill)
				progress["kills_parsed"] += 1
			else:
				continue 
			
		else:
			kill_data_dump(kill)
			progress["kills_parsed"] += 1
		#add attacker info later
			
	return progress

def kill_crawler_charRecord(start_killID,queryStr,progress):
	valid_kills = [] #join valid kills into one big query return
		
	
	JSON_obj = kill_fetch(start_killID,queryStr)
	
	for kill in JSON_obj:
		validKillFound=0
		if kill["victim"]["characterID"] == chracter_filter:
			continue
			
		for attacker in kill["attackers"]:
			if attacker["characterID"] == chracter_filter:
				if shiptype_filter == 0:
					validKillFound = 1
					break
				elif attacker["shipTypeID"] == shiptype_filter:
					validKillFound = 1
					break
				elif attacker["weaponTypeID"] == shiptype_filter:
					validKillFound = 1
					break
				else:
					continue
					
		if validKillFound == 1:
			valid_kills.append(kill)
		
	return progress
def kill_fetch(start_killID,queryStr):
	zkb_addr = "%sapi/beforeKillID/%s/%s" % (zkb_base,start_killID,queryStr)
	print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	headers=[]
	log_filehandle.write("%s:\tQuerying %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), zkb_addr))
	for tries in range (0,5):
		time.sleep(call_sleep_default*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
			raw_zip = opener.open(request)
			dump_zip_stream = raw_zip.read()
		except urllib2.HTTPError as e:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), er))
			print "URLError.  Retry %s: %s" %(zkb_addr,tries+1)
			continue
		except socket.error as err:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err))
			print "Socket Error.  Retry %s: %s" %(zkb_addr,tries+1)
			
		try:
			dump_IOstream = StringIO.StringIO(dump_zip_stream)
			zipper = gzip.GzipFile(fileobj=dump_IOstream)
			JSON_obj = json.load(zipper)
		except ValueError as errr:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), errr))
			print "Empty response.  Retry %s: %s" %(zkb_addr,tries+1)
			
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	
	if please_force==0:
		snooze_setter(header_hold)
	else:
		time.sleep(1)
	
	return JSON_obj
def kill_data_dump(kill_obj):
	global corporations,alliances,characters
	victim_corpID = kill_obj["victim"]["corporationID"]
	victim_charID = kill_obj["victim"]["characterID"]
	victim_allianceID = kill_obj["victim"]["allianceID"]
	
	if victim_corpID in corporations:
		corporations[victim_corpID]["losses"] += 1
		try:
			corporations[victim_corpID]["lossValue"] += kill_obj["zkb"]["totalValue"]
		except KeyError,e:
			pass
		if victim_charID not in corporations[victim_corpID]["members"]:
			corporations[victim_corpID]["members"].append(victim_charID)
	else:
		corporations[victim_corpID]={}
		corporations[victim_corpID]["losses"] = 1
		corporations[victim_corpID]["kills"] = 0
		corporations[victim_corpID]["members"] = []
		corporations[victim_corpID]["members"].append(victim_charID)
		corporations[victim_corpID]["corpName"] = kill_obj["victim"]["corporationName"]
		try:
			corporations[victim_corpID]["lossValue"] = kill_obj["zkb"]["totalValue"]
		except KeyError,e:
			corporations[victim_corpID]["lossValue"] = 0


def character_record_dump(valid_kill_list):
	test=1
	csv_table = []
	
	#dump to file (to avoid rescrape)	
	raw_zkb = open("raw_zkb.json",'w')
	raw_zkb.write(json.dumps(valid_kill_list,indent=4,sort_keys=True))
	
	csv_table[0] = ("killID","solarSystemID","killTime","victim_characterID",
		"victim_characterName","shipLost","reportedValue","involvedParties")
	for kill in valid_kill_list:
		csv_table_tmp = []
		csv_table_tmp [0] = kill["killID"]
		csv_table_tmp [1] = kill["solarSystemID"]
		csv_table_tmp [2] = kill["killTime"]
		csv_table_tmp [3] = kill["victim"]["characterID"]
		csv_table_tmp [4] = kill["victim"]["characterName"]
		csv_table_tmp [5] = kill["victim"]["shipTypeID"]
		csv_table_tmp [6] = kill["zkb"]["totalValue"]
		csv_table_tmp [7] = len(kill["attackers"])
	
def crash_handler(tracker_obj):
	try:
		with open(crash_file):
			pass#os.remove(crash_file)
	except IOError:	#want no file.  Create fresh each dump
		pass
	
	crash_handle = open (crash_file,'w')
	
	crash_handle.write(json.dumps(tracker_obj))
	crash_handle.close()
def main():
	global crash_obj
	init()
	parseargs()
	
	#crash_recover()
	
	print "-----Scraping zKB.  This may take a while-----"
	#print faction_filter
	initial_killID = feed_primer()
	progress = {}
	progress["killID"] = initial_killID
	progress["kills_parsed"] = 0
	progress["complete"] = 0
	progress["earlyDate"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	print "time\tkillID\tdateProgress\tKillsParsed"
	#while progress["complete"] ==0:
	#	time.sleep(call_sleep)
	#	progress = kill_crawler2(progress["killID"],zkb_query_str,progress)
	#	print "%s\t%s\t%s\t%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),progress["killID"],progress["earlyDate"],progress["kills_parsed"])
	#print "---------"
	#outfile = open("corp_results.csv",'w')
	#outfile.write( "ScrapeDate,%s,ScrapeTarget,%s\n" % (time.strftime("%Y-%m-%d", time.localtime()),start_date))
	#outfile.write( "corpID,corpName,losses,activeMemberCount,lossValue\n")
	#for corpID,info in corporations.iteritems():
	#	outfile.write( "%s,%s,%s,%s,%s\n" % (corpID,info["corpName"],info["losses"],len(info["members"]),info["lossValue"]))
	#outfile.close()
if __name__ == "__main__":
	main()
