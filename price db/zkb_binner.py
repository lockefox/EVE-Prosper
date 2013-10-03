#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json
import urllib2
import MySQLdb

systemlist="toaster_systemlist.json"	#system breakdown for destruction binning
lookup_file="lookup.json"				#ID->name conversion list
shiplist="toaster_shiplist.json"		#Allows stepping by groupID
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
db_name=""
db_schema=""
db=None
db_cursor=None


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
		if (len(existing_cols)-4 != len(systems["systemlist"].keys())): #check if bin count lines up
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
		request.add_header('Accept-encoding','gzip')
		request.add_header('User-Agent','eve-prosper.blogspot.com')	#Don't forget request headders
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
			global start_date
			start_date=arg
			try:	#Validate input
				time.strptime(start_date,"%Y-%m-%d")
			except ValueError as e:
				print e
				sys.exit(2)
		else:
			print "herp"

def feed_primer():	#initial fetch to initilaize crawler
	global start_killID
	
	zkb_primer_args = "losses/solo/limit/1/"
	zkb_addr = "%sapi/%s%s" % (zkb_base,zkb_primer_args,zkb_default_args)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-encoding','gzip')
	request.add_header('User-Agent','eve-prosper.blogspot.com')	#Don't forget request headders
	
	try:
		opener = urllib2.build_opener()
		headers = urllib2.urlopen(request).headers
	except urllib2.HTTPError as e:
		print e
		sys.exit(3)
	except urllib2.URLError as er:
		print er
		sys.exit(3)

	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	
	start_killID = JSON_obj[0]["killID"]	#"latest kill" in zKB
	return start_killID

def kill_crawler(start_killID,group,groupName):
	parsed_kills = 0
	
	zkb_primer_args = "losses/groupID/%s/limit/1/" % group
	zkb_addr = "%sapi/beforeKillID/%s/%s%s" % (zkb_base,start_killID,zkb_primer_args,zkb_default_args)
	#print zkb_addr
	request = urllib2.Request(zkb_addr)
	request.add_header('Accept-encoding','gzip')
	request.add_header('User-Agent','eve-prosper.blogspot.com')	#Don't forget request headders
	
	try:
		opener = urllib2.build_opener()
		headers = urllib2.urlopen(request).headers
	except urllib2.HTTPError as e:
		print e
		sys.exit(3)
	except urllib2.URLError as er:
		print er
		sys.exit(3)

	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	#print JSON_obj
	print headers
	
	next_killID=start_killID
	for kill in JSON_obj:
		next_killID=kill["killID"]
		ship_destroyed = kill["victim"]["shipTypeID"]
		date_killed = time.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		date_str = time.strftime("%Y-%m-%d",date_killed)
		print "killID %s:%s" % next_killID,date_str
		system_bins=[]
		for bin,system_list in systems["systemlist"].iteritems():
			if str(kill["solarSystemID"]) in system_list:		#str() needed, parses as INT default
				system_bins.append(bin)
		bin_line = ",".join(system_bins)
		table_line = "(date,typeID,typeName,typeCategory,%s)" % bin_line
		data = ",".join(["1"]*len(system_bins))
		value_line = "(%s,%s,%s,%s,%s)" % (date_str,ship_destroyed,lookup["types"][str(ship_destroyed)],"TBD",data)
		
		duplicate_case=""
		for bins in system_bins:
			duplicate_case+="%s = %s + 1, " % (bins,bins)
		duplicate_case = duplicate_case.rstrip(', ')
		print "INSERT INTO %s %s VALUES %s ON DUPLICATE KEY UPDATE %s" % (db_name,table_line,value_line,duplicate_case) #SHIP DATA
		
		cargo_report={}
		for cargo_items in kill["items"]:
			if cargo_items["qtyDestroyed"]>0:
				if cargo_items[str("typeID")] in cargo_report:	#Duplicate destroyed item
					cargo_report[str(cargo_items[str("typeID")])]+=cargo_items["qtyDestroyed"]
				else:											#New destroyed item
					cargo_report[str(cargo_items[str("typeID")])]=cargo_items["qtyDestroyed"]
		
		for key,value in cargo_report.iteritems():
			itemdata_line = ",".join([str(value)]*len(system_bins))
			data_line = "(%s,%s,%s,%s,%s)" % (date_str,key,lookup["types"][key],"TBD",itemdata_line)
			itemduplicate_case=""
			for bins in system_bins:
				itemduplicate_case+="%s = %s + %s, " % (bins,bins,value)
			itemduplicate_case = itemduplicate_case.rstrip(', ')
			print "INSERT INTO %s %s VALUES %s ON DUPLICATE KEY UPDATE %s" % (db_name,table_line,data_line,itemduplicate_case)
		parsed_kills+=1
	return parsed_kills
def main():
	init()
	parseargs()
	
	print "Scraping zKB.  This may take a while"
	for group,groupName in ship_list["groupID"].iteritems():
		start_killID = feed_primer()
		kills_parsed=kill_crawler(start_killID,group,groupName)
		print "Parsed %s: %s" %( groupName,kills_parsed)
		sys.exit(0)
if __name__ == "__main__":
	main()