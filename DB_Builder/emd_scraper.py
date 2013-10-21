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

def EMD_proc():
	item_todo=[]
	region_todo=[]
	item_progress={}
	
	## Set up todo lists ##
	if itemlist==None:
		#fetch full market list
		item_todo = lookup["types"].keys()
	else:
		item_todo = itemlist.split(',')
	
	try:
		with open(crash_file):
			print "recovering from %s" % crash_file
			crash_json=open(crash_file)
			crash_progress=json.load(crash_json)
			for item in item_todo:
				if item in crash_progress:
					if crash_progress[item]==1:
						item_todo.remove(item)
						item_progress[item]=1	#allow for repeated crashes
			pass
	except IOError:	
		print "no crash log found.  Executing as normal"
		pass	
	if regionlist==None:
		region_todo.append("10000002")
	else:
		region_todo = regionlist.split(',')
	dates_todo = days_2_dates(days)
	query_size = len(region_todo) * days
	max_query=5000
	items_per_query = math.floor(max_query/query_size)	#Group queries for fast loading
	if query_size > max_query:
		items_per_query=1
	progress=[0,len(item_todo)] #tracks progress
	
	print "Fetching histories from EVE-Marketdata"
	
	item_query_group=[]
	region_query=",".join(region_todo)
	item_query=""
	days_query=days
	result_data=[]		#[row],[date,region,typeName,typeid,"EMD",priceMax,priceMin,priceAverage,volume,orders,None,None]
	#result_data[]=[]

	for item in item_todo:
		item_query_group.append(item)
		progress[0]+=1
		item_progress[item]=0	#queried item

		if len(item_query_group)==items_per_query or (progress[0] + items_per_query) > len(item_todo):
			crash_handler(item_progress)
			EMD_URL = "http://api.eve-marketdata.com/api/item_history2.json?char_name=Lockefox&region_ids=%s&type_ids=%s&days=%s" % (region_query,",".join(item_query_group),days_query)
			print EMD_URL
			print "----"
			#print ",".join(item_query_group)
			response = urllib2.urlopen(EMD_URL).read()
			query_result = json.loads(response)
			hold_results=[]
			#real_results=[]
			item_dict={}
			for row_ittr in query_result["emd"]["result"]:	#Parse json into organized object
				result_line=result_line = [row_ittr["row"]["date"],row_ittr["row"]["regionID"],None,row_ittr["row"]["regionID"],\
					row_ittr["row"]["typeID"],"EMD",row_ittr["row"]["highPrice"],row_ittr["row"]["lowPrice"],row_ittr["row"]["avgPrice"],\
					row_ittr["row"]["volume"],row_ittr["row"]["orders"],None,None]
				#print result_line
				if row_ittr["row"]["typeID"] in item_dict:
					hold_line=item_dict[row_ittr["row"]["typeID"]]
					hold_line.append(result_line)
					item_dict[row_ittr["row"]["typeID"]]=hold_line
				else:
					item_dict[row_ittr["row"]["typeID"]]=[]
					item_dict[row_ittr["row"]["typeID"]].append(result_line)
				#key,value
			for item_key,results in item_dict.iteritems():		#Backfill missing dates, and write out to SQL
				#print results
				real_results=[]
				

				date_index=0
				previous_line=results[0]
				for date in dates_todo:
					line_found=0
					for line in results:
						if line[0]==date:
							tmp_result = [date,line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8],line[9],line[10],line[11],line[12]]
							real_results.append(tmp_result)
							previous_line=line
							line_found=1
							break
					if line_found==0:
						tmp_result=[date,previous_line[1],previous_line[2],previous_line[3],previous_line[4],"EMD_mod",previous_line[6],previous_line[7],previous_line[8],previous_line[9],previous_line[10],previous_line[11],previous_line[12]]
						real_results.append(tmp_result)
				#print real_results
				write_sql(real_results)
				item_progress[item_key]=1	#Completed query
			crash_handler(item_progress)
			item_query_group=[]
			display_progress(progress)
def crash_handler(completed_work):
	try:
		with open(crash_file):
			pass#os.remove(crash_file)
	except IOError:	#want no file.  Create fresh each dump
		pass
	
	crash_handle = open (crash_file,'w')
	
	crash_handle.write(json.dumps(completed_work))
	crash_handle.close()

	#sys.exit(1)
			
def display_progress(progress_list):
	progress_string = "%s of %s complete" % (progress_list[0], progress_list[1])
	sys.stdout.write(progress_string)
	sys.stdout.flush()
	sys.stdout.write("\b" * len(progress_string))
def write_sql(result_list):
	global db_cursor, db
	insert_string=""
	result_indx=0
	for line in result_list:
		print_list=[]
		#if result_indx==0:
		#	result_indx+=1
		#	continue
		for element in line:
			if element == None:
				print_list.append("NULL")
			else:
				print_list.append(element)
		#print print_list
		tmp_str="REPLACE %s (date,locationID,systemID,regionID,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose) VALUES('%s',%s,%s,%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s);" %(db_name,\
			print_list[0], print_list[1], print_list[2], print_list[3], print_list[4],\
			print_list[5], round(float(print_list[6]),2), round(float(print_list[7]),2), round(float(print_list[8]),2),\
			print_list[9], print_list[10], print_list[11], print_list[12])
			#date,locationID,systemID,regionID,typeID
			#source,priceMax,priceMin,priceAverage
			#volume,orders,priceOpen,priceClose
		#print tmp_str
		db_cursor.execute(tmp_str)
		db.commit()
		#try:
		#	db_cursor.execute(tmp_str)
		#except MySQLdb.IntegrityError as e:
		#	if (e[0] == 1062): #Table Already Exists
		#		print "%s entry exists already" % db_name
		#	else:
		#		raise e		
		#insert_string += "INSERT INTO %s (date,locationID,typeName,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose) VALUES('%s',%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s);\n" %(db_name,\
		#	print_list[0], print_list[1], print_list[2], print_list[3], print_list[4],\
		#	print_list[5], print_list[6], print_list[7], print_list[8], print_list[9],\
		#	print_list[10], print_list[11])
	#print insert_string
	#db_cursor.execute(insert_string)
	#db.commit()
	#db_cursor.close()
	#db_cursor=db.cursor()
	
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
			EMD_url = "%sapi/item_history2.json?char_name=%s&region_ids=%s&type_ids=%s&days=%s" % (EMD_base,User_Agent,region_string,item_str,days)
			#print EMD_url
			print "----------"
			EMD_return = EMD_fetch(EMD_url)
			results_raw = EMD_crunch(EMD_return)
			results_clean = result_process(results_raw)
			SQL_writer(results_clean)
			sys.exit(1)
			batch_item=[]
			continue
		elif batch_count == region_count:	#Clean up odd remainders
			item_str = ",".join(batch_item)
			EMD_url = "%sapi/item_history2.json?char_name=%s&region_ids=%s&type_ids=%s&days=%s" % (EMD_base,User_Agent,region_string,item_str,days)
			#print EMD_url
			print "----------"
			EMD_return = EMD_fetch(EMD_url)	
			results_raw = EMD_crunch(EMD_return)
			results_clean = result_process(results_raw)
			SQL_writer(results_clean)
			batch_item=[]
def SQL_writer (results):
	#Pushes data out to SQL
	global db_cursor, db
	
	for region,region_data in results.iteritems():
		date_indx=0
		for typeid,item_data in region_data.iteritems():
			#TODO: add EMD_mod cleanup
			
			for date_obj in item_data:
				date = date_obj.keys()[0]
				lowprice = results[region][typeid][date_indx][date]["lowPrice"]
				highprice = results[region][typeid][date_indx][date]["highPrice"]
				avgprice = results[region][typeid][date_indx][date]["avgPrice"]
				volume = results[region][typeid][date_indx][date]["volume"]
				orders = results[region][typeid][date_indx][date]["orders"]
				openprice = "NULL" #results[region][typeid][date_indx][date]["openPrice"]
				closeprice = "NULL" #results[region][typeid][date_indx][date]["closePrice"]
				source = results[region][typeid][date_indx][date]["source"]
						#'date',locationID,systemID,regionID,typeID,'source',priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose
				data_str = "'%s',%s,NULL,%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s" %\
					(date,region,region,typeid,source,highprice,lowprice,avgprice,volume,orders,openprice,closeprice)
				table_str = "date,locationID,systemID,regionID,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose"
				
				#print "REPLACE %s (%s) VALUES(%s)" % (db_table,table_str,data_str)
				
				db_cursor.execute("REPLACE %s (%s) VALUES(%s)" % (db_table,table_str,data_str))
				db.commit()
				
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
		print "feature incomplete.  --regionfast only"
	try:
		with open(crash_file):
			os.remove(crash_file)
	except IOError:	#want no file.  Create fresh each dump
		pass
	
if __name__ == "__main__":
	main()
	
def help():
	print "figure it out"