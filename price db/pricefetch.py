#!/Python27/python.exe

import sys,csv, sys, math, os, getopt, subprocess, math, datetime, time, json
import urllib2
import MySQLdb

########## INIT VARS ##########
db_cursor=None
EMD_base="http://eve-marketdata.com/"
EC_base="http://eve-central.com/"
lookup_json=open("lookup.json")
lookup=json.load(lookup_json)

########## GLOBALS ##########
regionlist=None	#comma separated list of regions (for EMD history)
systemlist=None	#comma separated list of systems (for EC history)
itemlist=None	#comma separated list of items (default to full list)
csv_only=0		#output CSV instead of SQL
sql_init_only=0	#output CSV CREATE file
sql_file="pricedata.sql"
EMD_parse=1		#run EMD history pull
EC_parse=0		#run EVE Central dump crunch
days=1
db_name=""
db_schema=""
def init():
	##Initialize DB cursor##
	if (csv_only==0 and sql_init_only==0):	
		global db_name,db_cursor,db_schema
		db_name="pricedata"
		db_schema="sdretribution11"
		db_IP="127.0.0.1"
		db_user="root"
		db_pw="bar"
		db_port=3306
		
		db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
		db_cursor = db.cursor()
		try:
			db_cursor.execute("CREATE TABLE %s (\
			`date` date NOT NULL,\
			`locationID` int(8) NOT NULL,\
			`typeName` varchar(45) NOT NULL,\
			`typeID` int(8) NOT NULL,\
			`source` varchar(8) NOT NULL,\
			`priceMax` float(8,2) DEFAULT NULL,\
			`priceMin` float(8,2) DEFAULT NULL,\
			`priceAverage` float(8,2) DEFAULT NULL,\
			`volume` int(16) DEFAULT NULL,\
			`orders` int(16) DEFAULT NULL,\
			`priceOpen` float(8,2) DEFAULT NULL,\
			`priceClose` float(8,2) DEFAULT NULL,\
			PRIMARY KEY (`date`,`locationID`,`typeID`,`source`))\
			ENGINE=InnoDB DEFAULT CHARSET=latin1" % db_name)
		except MySQLdb.OperationalError as e:
			if (e[0] == 1050): #Table Already Exists
				print "%s table already created" % db_name
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
	
	try:	#EVE-Central.com connection
		urllib2.urlopen(urllib2.Request(EC_base))
	except urllib2.URLError as e:
		print "Unable to connect to EVE-Central at %s" % EC_base
		print e.code
		sys.exit(4)
	except urllib2.HTTPError as er:
		print "Unable to connect to EVE-Central at %s" % EC_base
		print er.code
		sys.exit(4)
	print "EVE-Central connection:\t\tGOOD"
	
def parseargs():
	try:
		opts, args = getopt.getopt(sys.argv[1:],"rh:s:",["system=","region=","EMD","full","csv","items=","days="])
	except getopt.GetoptError:
		print "invalid arguments"
		#help()
		sys.exit(2)
		
	for opt, arg in opts:
		if opt == "-h":
			help()
		elif opt in ("-r","--region"):
			global regionlist
			regionlist=arg
		elif opt == "--EMD":
			global EMD_parse
			EMD_parse=1
		elif opt == "--csv":
			global csv_only
			csv_only=1
			print "function not fully supported yet"
		elif opt == "--days":
			global days
			days=int(arg)
			print days
		else:
			print "herp"

def EMD_proc():
	item_todo=[]
	region_todo=[]
	
	## Set up todo lists ##
	if itemlist==None:
		#fetch full market list
		item_todo = lookup["types"].keys()
	else:
		item_todo = itemlist.split(',')
		
	if regionlist==None:
		region_todo.append("10000002")
	else:
		region_todo = itemlist.split(',')
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
		if len(item_query_group)==items_per_query or (progress[0] + items_per_query) > len(item_todo):
			EMD_URL = "http://api.eve-marketdata.com/api/item_history2.json?char_name=Lockefox&region_ids=%s&type_ids=%s&days=%s" % (region_query,",".join(item_query_group),days_query)
			print ",".join(item_query_group)
			response = urllib2.urlopen(EMD_URL).read()
			query_result = json.loads(response)
			hold_results=[]
			real_results=[]
			for individual_item in item_query_group:	#write to SQL by individual item
				for row_ittr in query_result["emd"]["result"]:
					if int(row_ittr["row"]["typeID"]) != int(individual_item):
						continue
					result_line = [row_ittr["row"]["date"],row_ittr["row"]["regionID"],lookup["types"][row_ittr["row"]["typeID"]],row_ittr["row"]["typeID"],"EMD",row_ittr["row"]["highPrice"],row_ittr["row"]["lowPrice"],row_ittr["row"]["avgPrice"],row_ittr["row"]["volume"],row_ittr["row"]["orders"],None,None]
					#print result_line
					hold_results.append(result_line)
				date_indx=0
				previous_entry=hold_results[0] #IF T0 = null, then pass back earliest value to T0
				for result_ittr in hold_results:	#Clean up missing values
					if result_ittr[0]== dates_todo[date_indx]:	#found value
						real_results.append(result_ittr)
						date_indx+=1
						previous_entry=result_ittr
						continue
					else:										#Did not find value, use previous
						real_results.append(previous_entry)
						date_indx+=1
						previous_entry=result_ittr
				write_sql(real_results)
				sys.exit(1)
					
def write_sql(result_list):
	insert_string=""
	result_indx=0
	for line in result_list:
		print_list=[]
		if result_indx==0:
			result_indx+=1
			continue
		for element in line:
			if element == None:
				print_list.append("NULL")
			else:
				print_list.append(element)
		tmp_str="INSERT INTO %s.%s (date,locationID,typeName,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose) VALUES('%s',%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s);" %(db_schema,db_name,\
			print_list[0], print_list[1], print_list[2], print_list[3], print_list[4],\
			print_list[5], print_list[6], print_list[7], print_list[8], print_list[9],\
			print_list[10], print_list[11])
		
		#print tmp_str
		#db_cursor.execute(tmp_str)
		#try:
		#	db_cursor.execute(tmp_str)
		#except MySQLdb.IntegrityError as e:
		#	if (e[0] == 1062): #Table Already Exists
		#		print "%s entry exists already" % db_name
		#	else:
		#		raise e		
		insert_string += "INSERT INTO %s VALUES('%s',%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s);\n" %(db_name,\
			print_list[0], print_list[1], print_list[2], print_list[3], print_list[4],\
			print_list[5], print_list[6], print_list[7], print_list[8], print_list[9],\
			print_list[10], print_list[11])
	print insert_string
	db_cursor.execute(insert_string)
	
def days_2_dates (num_days):	#returns a strftime list of dates.  newest first (now, now-1d,...)
	list_of_dates=[]
	start_date = datetime.datetime.utcnow()
	while len(list_of_dates) < num_days:
		list_of_dates.append(start_date.strftime("%Y-%m-%d"))
		start_date += datetime.timedelta(days=-1)
		
	return list_of_dates
def main():
	parseargs()
	init()
	if EMD_parse==1:
		EMD_proc()
	
	
if __name__ == "__main__":
	main()
	
def help():
	print "figure it out"