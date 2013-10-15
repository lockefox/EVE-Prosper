#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

systemlist="toaster_systemlist.json"	#system breakdown for destruction binning
lookup_file="lookup.json"				#ID->name conversion list
shiplist="toaster_shiplist.json"		#Allows stepping by groupID
crash_file="binner_crash.json"			#tracks crashes for recovering gracefully
log_file = "binner_log.txt"				#Logs useful run data.  Moves old verson?
zkb_base="https://zkillboard.com/"
zkb_default_args="api-only/no-attackers/"
lookup_json = open(lookup_file)
system_json = open(systemlist)
ships_json = open(shiplist)
lookup = json.load(lookup_json)
systems= json.load(system_json)
ship_list=json.load(ships_json)

#Config File Globals
conf = ConfigParser.ConfigParser()
conf.read(["zkb.ini", "zkb_local.ini"])

########## GLOBALS ##########

csv_only=conf.get("GLOBALS", "csv_only")							#output CSV instead of SQL
sql_init_only=conf.get("GLOBALS", "sql_init_only")					#output CSV CREATE file
sql_file="pricedata.sql"

start_date=conf.get("GLOBALS", "startdate")
start_date_test=time.strptime(start_date,"%Y-%m-%d")
db_name=""
db_schema=""
db=None
db_cursor=None
User_Agent = "lockefox"
crash_obj={}
call_sleep_default=conf.get("GLOBALS", "default_sleep")	
call_sleep = call_sleep_default
log_filehandle = open(log_file, 'a+')

def init():
	global db_name,db_schema,db,db_cursor
	db_name=conf.get("DATABASE" ,"db_table")
	db_schema=conf.get("DATABASE" ,"db_name")
	db_IP=conf.get("DATABASE" ,"db_host")
	db_user=conf.get("DATABASE" ,"db_user")
	db_pw=conf.get("DATABASE" ,"db_pw")
	db_port=conf.getint("DATABASE" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
	db_cursor = db.cursor()
	
	db_cursor.execute("SHOW TABLES LIKE '%s'" % db_name)
	db_exists = len(db_cursor.fetchall())	#zero if not initialized
	#date,itemID,item_name,item_category,[locationbin]
	db_cols_match=1
	if db_exists:
		db_cursor.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS`  WHERE `TABLE_SCHEMA`='%s' AND `TABLE_NAME`='%s'" % (db_schema,db_name))
		existing_cols = db_cursor.fetchall()
		existing_cols_list = []
			
	else:	#Initialize DB
		try:
			db_cursor.execute( "CREATE TABLE %s (\
				`date` date NOT NULL,\
				`week` varchar(8) NOT NULL,\
				`typeID` int(8) NOT NULL,\
				`typeGroup` int(8) NOT NULL,\
				`systemID` int(8) NOT NULL,\
				`destroyed` int(16) DEFAULT 0,\
				PRIMARY KEY (`date`,`typeID`,`systemID`))\
				ENGINE=InnoDB DEFAULT CHARSET=latin1" % (db_name))
		except MySQLdb.OperationalError as e:
			if (e[0] == 1050): #Table Already Exists
				print "%s table already created" % db_name
			else:
				raise e		
	print "DB Connection:\t\tGOOD"
	
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
	time.sleep(10)
	
def parseargs():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"rh:s:",["system=","region=","csv","items=","startdate="])
	except getopt.GetoptError:
		print "invalid arguments"
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
	
	snooze_setter(header_hold)
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
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except socket.error as err:
			log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err))
			print "retry %s: %s" %(zkb_addr,tries+1)
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	

	snooze_setter(header_hold)

	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)


	if len(JSON_obj)==0:
		parsed_kills[2]=1
	next_killID=start_killID
	for kill in JSON_obj:
		parsed_kills[1]=kill["killID"]
		ship_destroyed = kill["victim"]["shipTypeID"]
		system = kill["solarSystemID"]
		date_killed = time.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		date_str = time.strftime("%Y-%m-%d",date_killed)
		if date_killed<start_date_test:		#Only process to desired date
			parsed_kills[2]=1
			break
		
		try:
			item_name=lookup["all_types"][str(ship_destroyed)]
		except KeyError as e:
			item_name=str(ship_destroyed)
			
		log_filehandle.write("%s:\t%s killID %s:%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),item_name,parsed_kills[1],date_str))
		
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

def snooze_setter(header):
	global call_sleep
	try:
		conn_allowance = int(header["X-Bin-Attempts-Allowed"])
		conn_reqs_used = int(header["X-Bin-Requests"])
		conn_sleep_time= int(header["X-Bin-Seconds-Between-Request"])
	except KeyError as e:
		print "WARNING: %s" % e
		call_sleep = call_sleep_default
		print header_hold
	
	if (conn_reqs_used+1)==conn_allowance:
		call_sleep = conn_sleep_time #full back-off if allowance is out
	##### Polite Scheme.  Need to speed/fail test
	#elif conn_reqs_used > 1:
	#	call_sleep = (conn_sleep_time/conn_allowance)*conn_reqs_used #slow down if using up some budget
	#############################################
	else:
		call_sleep = 0 #conn_sleep_time/5		#Go as fast as possible
	#print "X-Bin-Attempts-Allowed: %s" % conn_allowance
	#print "X-Bin-Requests: %s" % conn_reqs_used
	#print "X-Bin-Seconds-Between-Request: %s" % conn_sleep_time
		
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
	
	crash_recover()
	
	print "-----Scraping zKB.  This may take a while-----"
	for group,groupName in ship_list["groupID"].iteritems():
		start_killID=0		
		if group in crash_obj["parsed_data"]:
			if crash_obj["parsed_data"][group] == "done":
				print "Group %s already complete" % groupName
				continue
			else:
				start_killID = crash_obj["parsed_data"][group]
        
		else:
			start_killID = feed_primer()
			
		kills_parsed=[0,start_killID,0] #Progress,killID,done
		crash_obj["parsed_data"][group]=start_killID	#If fail first 
		crash_handler(crash_obj)
		
		while kills_parsed[2]==0:
			time.sleep(call_sleep)
			kills_parsed=kill_crawler(kills_parsed[1],group,groupName,kills_parsed[0]) #list allows passing by reference.  Control 3 return values
			crash_obj["parsed_data"][group]=kills_parsed[1]
			crash_handler(crash_obj)
			print "Parsed %s: %s sleep=%s" %( groupName,kills_parsed,call_sleep)
			
		crash_obj["parsed_data"][group]="done"	#once complete, log as "done"
		crash_handler(crash_obj)
if __name__ == "__main__":
	main()
