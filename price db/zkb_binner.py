#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json
import urllib2
import MySQLdb

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


########## GLOBALS ##########

csv_only=0								#output CSV instead of SQL
sql_init_only=0							#output CSV CREATE file
sql_file="pricedata.sql"

start_date="2013-01-01"
start_date_test=time.strptime(start_date,"%Y-%m-%d")
db_name=""
db_schema=""
db=None
db_cursor=None
User_Agent = "not-Lockefox"
crash_obj={}

def init():
	global db_name,db_schema,db,db_cursor
	db_name="killdata"
	db_schema="odyssey-1.1-91288"
	db_IP="127.0.0.1"
	db_user="root"
	db_pw="bar"
	db_port=3306
	
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
		for value in existing_cols:		#reduce fetchall() result to 1D list
			existing_cols_list.append(value[0])
		if (len(existing_cols)-6 != len(systems["systemlist"].keys())): #check if bin count lines up
			db_cols_match=0
			print "Number of columns in EXISTING table does not match bins in %s" % systemlist
			print "please manually DROP %s from %s" % db_name,db_schema
			
			#CASE FOR DB exists, but BINS might have changed
		for bin,sys_list in systems["systemlist"].iteritems():
			if (bin not in existing_cols_list):
				db_cols_match=0
				print "%s not found in existing db" % aug_bin
				print "please manually DROP %s from %s" % db_name,db_schema
				sys.exit(2)
	
	else:	#Initialize DB
		bin_str=""
		for bin,sys_list in systems["systemlist"].iteritems():
			bin_str+="`%s` int(16) DEFAULT NULL,"%(bin)
		try:
			db_cursor.execute( "CREATE TABLE %s (\
				`date` date NOT NULL,\
				`typeID` int(8) NOT NULL,\
				`typeName` varchar(100) NOT NULL,\
				`typeCategory` int(8) NOT NULL,\
				`typeGroup` int(8) NOT NULL,\
				`TotalDestroyed` bigint(32) NOT NULL,\
				%s\
				PRIMARY KEY (`date`,`typeID`))\
				ENGINE=InnoDB DEFAULT CHARSET=latin1" % (db_name,bin_str))
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
	
	zkb_primer_args = "losses/solo/limit/1/"
	zkb_addr = "%sapi/%s%s" % (zkb_base,zkb_default_args,zkb_primer_args)
	print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	
	headers=[]
	for tries in range (0,5):
		time.sleep(5*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
		except urllib2.HTTPError as e:
			print e
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			print er
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)

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
	parsed_kills = [progress,start_killID,0]
	
	zkb_primer_args = "losses/groupID/%s/" % group
	zkb_addr = "%sapi/beforeKillID/%s/%s%s" % (zkb_base,start_killID,zkb_default_args,zkb_primer_args)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)	#Don't forget request headders
	headers=[]
	for tries in range (0,5):
		time.sleep(5*tries)
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			headers.append(header_hold)
		except urllib2.HTTPError as e:
			print e
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			print er
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		else:
			break
	else:
		print "unable to open %s after %s tries" % (zkb_addr,tries+1)
		print headers
		sys.exit(4)
	
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	#print JSON_obj
	print headers
	if len(JSON_obj)==0:
		parsed_kills[2]=1
	next_killID=start_killID
	for kill in JSON_obj:
		parsed_kills[1]=kill["killID"]
		ship_destroyed = kill["victim"]["shipTypeID"]
		date_killed = time.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		date_str = time.strftime("%Y-%m-%d",date_killed)
		if date_killed<start_date_test:		#Only process to desired date
			parsed_kills[2]=1
			break
		print "killID %s:%s" % (parsed_kills[1],date_str)
		system_bins=[]
		for bin,system_list in systems["systemlist"].iteritems():
			if str(kill["solarSystemID"]) in system_list:		#str() needed, parses as INT default
				system_bins.append(bin)
		bin_line = ",".join(system_bins)
		table_line = "(date,typeID,typeName,typeCategory,typeGroup,TotalDestroyed,%s)" % bin_line
		data = ",".join(["1"]*len(system_bins))
		value_line = "('%s',%s,'%s',%s,%s,%s,%s)" % (date_str,ship_destroyed,lookup["all_types"][str(ship_destroyed)],0,group,1,data)
		
		duplicate_case=""
		for bins in system_bins:
			duplicate_case+="%s = IFNULL(%s,0) + 1, " % (bins,bins)
		duplicate_case = duplicate_case.rstrip(', ')
		db_cursor.execute("INSERT INTO %s %s VALUES %s ON DUPLICATE KEY UPDATE TotalDestroyed = TotalDestroyed+1, %s" % (db_name,table_line,value_line,duplicate_case)) #SHIP DATA
		db.commit()
		
		cargo_report={}
		for cargo_items in kill["items"]:
			if cargo_items["qtyDestroyed"]>0:
				if cargo_items[str("typeID")] in cargo_report:	#Duplicate destroyed item
					cargo_report[str(cargo_items[str("typeID")])]+=cargo_items["qtyDestroyed"]
				else:											#New destroyed item
					cargo_report[str(cargo_items[str("typeID")])]=cargo_items["qtyDestroyed"]
		
		for key,value in cargo_report.iteritems():
			itemdata_line = ",".join([str(value)]*len(system_bins))
			try:
				data_line = "('%s',%s,'%s',%s,%s,%s,%s)" % (date_str,key,lookup["all_types"][key],0,0,value,itemdata_line)
			except KeyError as e:	#If I don't have the key, it's not worth tracking
				print "unable to find %s" % key
				continue
			itemduplicate_case=""
			for bins in system_bins:
				itemduplicate_case+="%s = IFNULL(%s,0) + %s, " % (bins,bins,value)
			itemduplicate_case = itemduplicate_case.rstrip(', ')
			#print "\tINSERT INTO %s %s VALUES %s ON DUPLICATE KEY UPDATE TotalDestroyed = TotalDestroyed+%s, %s" % (db_name,table_line,data_line,value,itemduplicate_case)
			db_cursor.execute("INSERT INTO %s %s VALUES %s ON DUPLICATE KEY UPDATE TotalDestroyed = TotalDestroyed+%s, %s" % (db_name,table_line,data_line,value,itemduplicate_case))
			db.commit()
			#31093574
			#31093474
		parsed_kills[0]+=1
		sys.exit(1)
		print "-------"
	
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
		validate_delete = raw_input("Delete all entries to %s?  (Y/N)" % start_date)
		if validate_delete.upper() == 'Y':
			db_cursor.execute("DELETE FROM %s WHERE date>='%s'" % (db_name,start_date))
			db.commit()
			print "\tCleaning up ALL entries to %s" % start_date
		else:
			print "\tWARNING: values may be wrong without scrubbing duplicates"
			time.sleep(5)
			#Initialize crash_obj
		crash_obj={}
		crash_obj["parsed_data"]={}
			
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
			time.sleep(25)
			kills_parsed=kill_crawler(kills_parsed[1],group,groupName,kills_parsed[0]) #list allows passing by reference.  Control 3 return values
			crash_obj["parsed_data"][group]=kills_parsed[1]
			crash_handler(crash_obj)
			print "Parsed %s: %s" %( groupName,kills_parsed)
		crash_obj["parsed_data"][group]="done"	#once complete, log as "done"
		crash_handler(crash_obj)
if __name__ == "__main__":
	main()