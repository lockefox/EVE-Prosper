#!/Python27/python.exe

import sys, math, os, getopt, subprocess, math, datetime, time, json
import urllib2
import MySQLdb
import ConfigParser

########## INIT VARS ##########
EMD_base = "http://eve-marketdata.com/"
lookup_json = open("lookup.json")
lookup = json.load(lookup_json)
crash_file = "emd_scraper_crash.json"
crash_obj={}

#Config File Globals
conf = ConfigParser.ConfigParser()
conf.read(["scraper.ini", "scraper_local.ini"])

########## GLOBALS ##########
regionlist = None	#comma separated list of regions (for EMD history)
systemlist = None	#comma separated list of systems (for EC history)
itemlist = None		#comma separated list of items (default to full list)
csv_only = int(conf.get("GLOBALS","csv_only"))				#output CSV instead of SQL
sql_init_only = int(conf.get("GLOBALS","sql_init_only"))	#output CSV CREATE file
region_fast = int(conf.get("EMD","region_fast"))			#Loop scheme: region-fast or item-fast
days = int(conf.get("EMD","default_days"))
query_limit = int(conf.get("EMD","query_limit"))
User_Agent = conf.get("EMD","user_agent")

########## DB VARS ##########
db_table = conf.get("EMD","db_table")
db_name = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))
db_cursor = None
db = None


def init():
	##Initialize DB cursor##
	global crash_obj
	if (csv_only==0 and sql_init_only==0):	
		global db_cursor, db
		
		db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_name)
		
		db_cursor = db.cursor()
		try:
			db_cursor.execute("CREATE TABLE %s (\
			`date` date NOT NULL,\
			`locationID` int(8) NOT NULL,\
			`systemID` int(8) DEFAULT NULL,\
			`regionID` int(8) DEFAULT NULL,\
			`typeID` int(8) NOT NULL,\
			`source` varchar(8) NOT NULL,\
			`priceMax` float(16,4) DEFAULT NULL,\
			`priceMin` float(16,4) DEFAULT NULL,\
			`priceAverage` float(16,4) DEFAULT NULL,\
			`volume` bigint(32) unsigned DEFAULT NULL,\
			`orders` int(16) DEFAULT NULL,\
			`priceOpen` float(16,4) DEFAULT NULL,\
			`priceClose` float(16,4) DEFAULT NULL,\
			PRIMARY KEY (`date`,`locationID`,`typeID`,`source`))\
			ENGINE=InnoDB DEFAULT CHARSET=latin1" % db_table)
		except MySQLdb.OperationalError as e:
			if (e[0] == 1050): #Table Already Exists
				print "%s table already created" % db_table
			else:
				raise e		
		print "DB Connection:\t\t\tGOOD"
	else:
		print "DB connection:\t\t\tSKIPPED"
		
	##TEST Internet connection and resource connection##
	try:	#EVE-Marketdata.com connection
		urllib2.urlopen(urllib2.Request(EMD_base))
	except urllib2.URLError as e:
		print "Unable to connect to EMD at %s" % EMD_base
		print e.code
		sys.exit(4)
	except urllib2.HTTPError as er:
		print "Unable to connect to EMD at %s" % EMD_base
		print er.code
		sys.exit(4)
	print "EVE-Marketdata connection:\tGOOD"
	
	## Initialize or load crash handler ##
	try:
		with open(crash_file):
			print "Recovering from: %s" % crash_file
			crash_json = open(crash_file)
			crash_obj = json.load(crash_json)
			pass
	except IOError:
		print "No crash log found.  Initializing fresh run"
		crash_obj = {}
		crash_obj ["progress_list"] = {}
		crash_obj ["queries_run"] = {}
		
def parseargs():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"rh:s:",["system=","region=","regionfast","itemfast","full","csv","items=","days="])
	except getopt.GetoptError:
		print "invalid arguments"
		#help()
		sys.exit(2)
	global region_fast		
	for opt, arg in opts:
		if opt == "-h":
			help()
		elif opt in ("-r","--region"):
			global regionlist
			regionlist=arg
		elif opt == "--csv":
			global csv_only
			csv_only=1
			print "function not fully supported yet"
		elif opt == "--days":
			global days
			days=int(arg)
			print days
		elif opt =="--regionfast":
			region_fast=1
		elif opt =="--itemfast":	#default
			region_fast=0
		else:
			print "herp"


def crash_handler(completed_work):
	try:
		with open(crash_file):
			pass#os.remove(crash_file)
	except IOError:	#want no file.  Create fresh each dump
		pass
	
	crash_handle = open (crash_file,'w')
	crash_handle.write(json.dumps(completed_work,sort_keys=True,indent=4))
	crash_handle.close()

def repeat_scrubber (region_string, item_string):
	global crash_obj
	
	region_list = region_string.split(',')
	item_list = item_string.split(',')		#Could have imported lists, but whatever
	
	tmp_region_list = region_list
	tmp_item_list = item_list
	
	find_matrix = []
	#####		item1	item2	item3
	#####region1 [x]			 [x]
	#####region2 [x]	[x]		 [x]	del region2
	#####region3 [x]	[x]			
	#####	 del item1
	conditioned_string="&region_ids=%s&type_ids=%s" % (region_string, item_string)
	if conditioned_string in crash_obj["queries_run"]:
		return None
	#loads checker
	#region_index=0
	#for region in region_list:
	#	find_matrix.append([])
	#	for item in item_list:
	#		if region in crash_obj["progress_list"]:
	#			if item in crash_obj["progress_list"][region]:
	#				if crash_obj["progress_list"][region][item]==1:
	#					find_matrix[region_index].append(1)
	#			else:
	#				find_matrix[region_index].append(0)
	#		else:
	#			find_matrix[region_index].append(0)
	#	region_index+=1
	#
	##remove regions
	#region_index=0
	#max_len = 0
	##print region_list
	#for row in find_matrix:
	#	#print "scrubbing regions"
	#	skip_region = 1
	#	if len(row) > max_len:	#I am bad at code and impatient.  enjoy CS101 solution
	#		max_len = len(row)
	#	for col in row:
	#		if col == 0:
	#			skip_region = 0
	#	if skip_region == 1:
	#		
	#		region_to_skip = region_list[region_index]
	#		tmp_region_list.remove(region_to_skip)
	#	region_index+=1
    #
	#item_index=0
	#for col in range(max_len):
	#	#print "scrubbing items"
	#	skip_item = 1
	#	for row in find_matrix:
	#		if row[col] == 0:
	#			skip_item=0
	#	if skip_item == 1:
	#		item_to_skip = item_list[item_index]
	#		tmp_item_list.remove(item_to_skip)
	#	item_index+=1
	#
	#if (len(tmp_item_list)==0 or len(tmp_item_list)==0):
	#	conditioned_string = None
	#else:
	#	conditioned_string="&region_ids=%s&type_ids=%s" % (",".join(tmp_region_list),",".join(tmp_item_list))
	

	
	return conditioned_string

	
def region_fast_scrape(region_string, region_number):
	items_todo = []
	item_str = ""
	
	if itemlist == None:	#use JSON
		items_todo=lookup["types"].keys()
	else:					#use user-input
		item_todo=itemlist.split(',')
		
	##TODO crash handler
	
	item_limit = math.floor(query_limit/(days*region_number))
	
	batch_item=[]
	batch_count=0
	EMD_return = {}
	for item in items_todo:
		batch_item.append(item)
		batch_count += 1
		if len(batch_item) == item_limit:
			item_str = ",".join(batch_item)
			region_item_str = repeat_scrubber(region_string,item_str)
			if region_item_str == None:
				print "skipping regions:%s x items:%s" % (region_string,item_str)
				batch_item=[]
				continue
			EMD_url = "%sapi/item_history2.json?char_name=%s%s&days=%s" % (EMD_base,User_Agent,region_item_str,days)
			#print EMD_url
			EMD_return = EMD_fetch(EMD_url)
			print "----------"
			results_raw = EMD_crunch(EMD_return)
			if results_raw == None:
				print "no data returned"
				print "----------"
				batch_item=[]
				continue
			results_clean = result_process(results_raw)
			SQL_writer(results_clean,region_item_str)
			batch_item=[]
			continue
		elif batch_count == region_number:	#Clean up odd remainders
			item_str = ",".join(batch_item)
			region_item_str = repeat_scrubber(region_string,item_str)
			if region_item_str == None:
				print "skipping regions:%s x items:%s" % (region_string,item_str)
				batch_item=[]
				print "----------"
				continue
			EMD_url = "%sapi/item_history2.json?char_name=%s%s&days=%s" % (EMD_base,User_Agent,region_item_str,days)
			#print EMD_url
			EMD_return = EMD_fetch(EMD_url)	
			results_raw = EMD_crunch(EMD_return)
			if results_raw == None:
				print "no data returned"
				batch_item=[]
				print "----------"
				continue
			results_clean = result_process(results_raw)
			SQL_writer(results_clean,region_item_str)
			batch_item=[]
			print "----------"
			
def item_fast_scrape(item_string,item_number):
	region_todo = []
	region_str = ""
	
	if regionlist == None:	#use JSON
		region_todo = lookup["regions_scrape"]
	else: 					#user input
		region_todo = regionlist.split(',')
		
	#TODO crash handler
	
	region_limit = math.floor(query_limit/(days*item_number))
	
	batch_region = []
	batch_count = 0
	EMD_return = {}
	for region in region_todo:
		batch_region.append(region)
		batch_count += 1
		if len(batch_region) == region_limit:
			region_str = ",".join(batch_region)
			region_item_str = repeat_scrubber(region_str,item_string)
			if region_item_str == None:
				print "skipping regions:%s x items:%s" % (region_str,item_string)
				batch_region=[]
				print "----------"
				continue
			EMD_url = "%sapi/item_history2.json?char_name=%s%s&days=%s" % (EMD_base,User_Agent,region_item_str,days)
			#print EMD_url
			EMD_return = EMD_fetch(EMD_url)

			results_raw = EMD_crunch(EMD_return)
			if results_raw == None:
				print "no data returned"
				batch_region=[]
				print "----------"
				continue
			results_clean = result_process(results_raw)
			SQL_writer(results_clean,region_item_str)
			batch_region=[]
			print "----------"
			continue
		elif batch_count == item_number:
			region_str = ",".join(batch_item)
			region_item_str = repeat_scrubber(region_str,item_string)
			if region_item_str == None:
				print "skipping regions:%s x items:%s" % (region_str,item_string)
				batch_region=[]
				print "----------"
				continue
			EMD_url = "%sapi/item_history2.json?char_name=%s%s&days=%s" % (EMD_base,User_Agent,region_item_str,days)
			#print EMD_url
			EMD_return = EMD_fetch(EMD_url)
			results_raw = EMD_crunch(EMD_return)
			if results_raw == None:
				print "no data returned"
				batch_region=[]
				print "----------"
				continue
			results_clean = result_process(results_raw)
			SQL_writer(results_clean,region_item_str)
			batch_region=[]
			print "----------"
						
def SQL_writer (results,EMD_query):
	#Pushes data out to SQL
	global db_cursor, db, crash_obj
	table_str = "date,locationID,systemID,regionID,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose"
	commit_str = "REPLACE %s (%s) VALUES" % (db_table,table_str)
	crash_obj["queries_run"][EMD_query]=1
	for region,region_data in results.iteritems():
		if crash_obj["progress_list"].get(region) == None:
			crash_obj["progress_list"][region]={}
		for typeid,item_data in region_data.iteritems():
			#if crash_obj[region].get(typeid) == None:
			crash_obj["progress_list"][region][typeid]=1
			
			#TODO: add EMD_mod cleanup
			date_indx=0
			for date_obj in item_data:
				date = date_obj.keys()[0]
				lowprice = results[region][typeid][date_indx][date]["lowPrice"]
				highprice = results[region][typeid][date_indx][date]["highPrice"]
				avgprice = results[region][typeid][date_indx][date]["avgPrice"]
				volume = results[region][typeid][date_indx][date]["volume"]
				orders = results[region][typeid][date_indx][date]["orders"]
				openprice = "NULL" #TODO: None to NULL conversion results[region][typeid][date_indx][date]["openPrice"]
				closeprice = "NULL" #results[region][typeid][date_indx][date]["closePrice"]
				source = results[region][typeid][date_indx][date]["source"]
						#'date',locationID,systemID,regionID,typeID,'source',priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose
				data_str = "'%s',%s,NULL,%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s" %\
					(date,region,region,typeid,source,highprice,lowprice,avgprice,volume,orders,openprice,closeprice)
				commit_str += " (%s)," % data_str
				
				date_indx+=1
				
	commit_str = commit_str.rstrip(',') #clean up trailing comma
	#print commit_str
	try:
		db_cursor.execute(commit_str)	#dumps whole EMD result into db at once
	except MySQLdb.ProgrammingError as er:
		print commit_str
		sys.exit(5)
	db.commit()
	
	crash_handler(crash_obj)
				
def result_process(results):
	#Takes result object and backfills missing values
	for region,region_data in results.iteritems():
		for typeid,item_data in region_data.iteritems():
			date_indx = 0
			#print results[region][typeid]
			for date_obj in item_data:
				date = date_obj.keys()[0]
				if len(date_obj[date])==0:	#if object is empty
					if date_indx == 0:	#start of object is empty
						results[region][typeid][date_indx][date]["regionID"] = region
						results[region][typeid][date_indx][date]["typeID"] = typeid
						results[region][typeid][date_indx][date]["date"] = date
						results[region][typeid][date_indx][date]["lowPrice"] = 0
						results[region][typeid][date_indx][date]["highPrice"] = 0
						results[region][typeid][date_indx][date]["avgPrice"] = 0
						results[region][typeid][date_indx][date]["volume"] = 0
						results[region][typeid][date_indx][date]["orders"] = 0
						results[region][typeid][date_indx][date]["openPrice"] = None
						results[region][typeid][date_indx][date]["closePrice"] = None
						results[region][typeid][date_indx][date]["source"] = "EMD_mod"
					else:	#use previous entry otherwise (feed forward 0's)
						prev_date = results[region][typeid][date_indx-1].keys()[0]
						lowprice = results[region][typeid][date_indx-1][prev_date]["lowPrice"]
						highprice = results[region][typeid][date_indx-1][prev_date]["highPrice"]
						avgprice = results[region][typeid][date_indx-1][prev_date]["avgPrice"]
						volume = results[region][typeid][date_indx-1][prev_date]["volume"]
						orders = results[region][typeid][date_indx-1][prev_date]["orders"]
						
						results[region][typeid][date_indx][date]["regionID"] = region
						results[region][typeid][date_indx][date]["typeID"] = typeid
						results[region][typeid][date_indx][date]["date"] = date
						results[region][typeid][date_indx][date]["lowPrice"] = lowprice
						results[region][typeid][date_indx][date]["highPrice"] = highprice
						results[region][typeid][date_indx][date]["avgPrice"] = avgprice
						results[region][typeid][date_indx][date]["volume"] = volume
						results[region][typeid][date_indx][date]["orders"] = orders
						results[region][typeid][date_indx][date]["openPrice"] = None
						results[region][typeid][date_indx][date]["closePrice"] = None
						results[region][typeid][date_indx][date]["source"] = "EMD_mod"

				date_indx+=1
	return results
	
def EMD_crunch(EMD_JSON):
	#Parses return object from EMD and conditions for writing to the DB
	dates_todo = days_2_dates(days)	#convert #days into list of dates
	
	#results{region}{item}=[{date:{hi,low,avg,vol,ord,date}},{date:{hi,low,avg,vol,ord,date}}]
	results={}
	if len(EMD_JSON) == 0:	#No data returned, skip processing
		return None
	for entry in EMD_JSON:
		region = int(entry["row"]["regionID"])
		typeid = int(entry["row"]["typeID"])
		entry_date = str(entry["row"]["date"])
		lowprice = float(entry["row"]["lowPrice"])
		highprice = float(entry["row"]["highPrice"])
		avgprice = float(entry["row"]["avgPrice"])
		volume = int(entry["row"]["volume"])
		orders = int(entry["row"]["volume"])
		openprice = None		#used for SQL write step
		closeprice = None 		#used for SQL write step
		
		#Initialize result structure before parsing
		if results.get(region)==None:
			results[region]={}
		if results[region].get(typeid)==None:
			results[region][typeid]= []
			tmp_indx=0
			for date in dates_todo:
				item_object = {}
				item_object[date]={}
				results[region][typeid].append(item_object)
			
		result_index = 0
		for element in results[region][typeid]:
			indx_date = element.keys()
			if indx_date[0] == entry_date:
				break
			else:
				result_index+=1

		#Load data into structure
		results[region][typeid][result_index][entry_date]["regionID"] = region
		results[region][typeid][result_index][entry_date]["typeID"] = typeid
		results[region][typeid][result_index][entry_date]["date"] = entry_date
		results[region][typeid][result_index][entry_date]["lowPrice"] = lowprice
		results[region][typeid][result_index][entry_date]["highPrice"] = highprice
		results[region][typeid][result_index][entry_date]["avgPrice"] = avgprice
		results[region][typeid][result_index][entry_date]["volume"] = volume
		results[region][typeid][result_index][entry_date]["orders"] = orders
		results[region][typeid][result_index][entry_date]["openPrice"] = openprice
		results[region][typeid][result_index][entry_date]["closePrice"] = closeprice
		results[region][typeid][result_index][entry_date]["source"] = "EMD"	
	
	return results
	
def EMD_fetch(url):
	#queries EMD and returns the JSON
	print url
	
	for tries in range (0,5):
		time.sleep(10*tries)
		try:
			response = urllib2.urlopen(url).read()
		except urllib2.HTTPError as e:
			print "retry %s: %s" % (url,tries)
			continue
		except urllib2.URLError as er:
			print "retry %s: %s" % (url,tries)
			continue
		else:
			break
	else:
		print "unable to open %s after %s tries" % (url, tries)
		sys.exit(4)
	EMD_json = json.loads(response)	
	
	return EMD_json["emd"]["result"]
	

def days_2_dates (num_days):	#returns a strftime list of dates.  newest first (now, now-1d,...)
	list_of_dates=[]
	start_date = datetime.datetime.utcnow()
	while len(list_of_dates) < num_days:
		list_of_dates.append(start_date.strftime("%Y-%m-%d"))
		start_date += datetime.timedelta(days=-1)
	list_of_dates.reverse()
	return list_of_dates
def main():
	parseargs()
	init()
	#if EMD_parse==1:
	#	EMD_proc()
	#print "EMD Data parsed successfully"
	
	if region_fast==1:
		region_todo = []	#holds -region=str
		region_n = 0		#helps calculate query limit
		region_str = ""
		
		if regionlist == None:	#use JSON
			region_todo = lookup["regions_scrape"]
		else: 					#user input
			region_todo = regionlist.split(',')
			
		region_limit = math.floor(query_limit/days)
		region_count = len(region_todo)
		batch_region = []
		batch_count = 0
		for region in region_todo:	#JSON has regions in array for "priority order"
			batch_region.append(region)
			batch_count += 1
			
			if len(batch_region)==region_limit:					#Batch regions so at least 1 item/query can run
				region_str = ",".join(batch_region)
				region_n = len(batch_region)
				region_fast_scrape(region_str,region_n)	
				batch_region = []
				continue				
			elif batch_count==region_count:	#clean up remainder in one pass
				region_str = ",".join(batch_region)
				region_n = len(batch_region)
				region_fast_scrape(region_str,region_n)	
				batch_region = []
				#loop should finish here
	else:		#Item Fast
		item_todo = []
		item_n = 0
		item_str = ""
		
		if itemlist == None:
			item_todo = lookup["types"].keys()
		else:
			item_todo = itemlist.split(',')
			
		item_limit = math.floor(query_limit/days)
		item_count = len(item_todo)
		batch_item = []
		batch_count = 0
		for item in item_todo:
			batch_item.append(item)
			batch_count +=1
			
			if len(batch_item) == item_limit:
				item_str = ",".join(batch_item)
				item_n = len(batch_item)
				item_fast_scrape(item_str,item_n)
				batch_region = []
				continue
			elif batch_count == item_count:
				item_str = ",".join(batch_item)
				item_n = len(batch_item)
				item_fast_scrape(item_str,item_n)
				batch_region = []
				
	try:
		with open(crash_file):
			crash_file.close()
			os.remove(crash_file)
	except IOError:	#want no file.  Create fresh each dump
		pass
	
if __name__ == "__main__":
	main()
	
def help():
	print "figure it out"