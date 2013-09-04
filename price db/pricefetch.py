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
db=None
def init():
	##Initialize DB cursor##
	if (csv_only==0 and sql_init_only==0):	
		global db_name,db_cursor,db_schema, db
		db_name="pricedata"
		db_schema="sdretribution11"
		db_IP="127.0.0.1"
		db_user="root"
		db_pw="bar"
		db_port=3306
		
		db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		#db.autocommit()
		
		db_cursor = db.cursor()
		try:
			db_cursor.execute("CREATE TABLE %s (\
			`date` date NOT NULL,\
			`locationID` int(8) NOT NULL,\
			`typeName` varchar(100) NOT NULL,\
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
	if EMD_parse == 1:
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
	if EC_parse == 1:
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
			print EMD_URL
			print "----"
			#print ",".join(item_query_group)
			response = urllib2.urlopen(EMD_URL).read()
			query_result = json.loads(response)
			hold_results=[]
			#real_results=[]
			item_dict={}
			for row_ittr in query_result["emd"]["result"]:	#Parse json into organized object
				result_line=result_line = [row_ittr["row"]["date"],row_ittr["row"]["regionID"],lookup["types"][row_ittr["row"]["typeID"]],\
					row_ittr["row"]["typeID"],"EMD",row_ittr["row"]["highPrice"],row_ittr["row"]["lowPrice"],row_ittr["row"]["avgPrice"],\
					row_ittr["row"]["volume"],row_ittr["row"]["orders"],None,None]
				if row_ittr["row"]["typeID"] in item_dict:
					hold_line=item_dict[row_ittr["row"]["typeID"]]
					hold_line.append(result_line)
					item_dict[row_ittr["row"]["typeID"]]=hold_line
				else:
					item_dict[row_ittr["row"]["typeID"]]=[]
					item_dict[row_ittr["row"]["typeID"]].append(result_line)
				#key,value
			for item,results in item_dict.iteritems():		#Backfill missing dates, and write out to SQL
				#print results
				real_results=[]
				

				date_index=0
				previous_line=results[0]
				for date in dates_todo:
					line_found=0
					for line in results:
						if line[0]==date:
							tmp_result = [date,line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8],line[9],line[10],line[11]]
							real_results.append(tmp_result)
							previous_line=line
							line_found=1
							break
					if line_found==0:
						tmp_result=[date,previous_line[1],previous_line[2],previous_line[3],"EMD_mod",previous_line[5],previous_line[6],previous_line[7],previous_line[8],previous_line[9],previous_line[10],previous_line[11]]
						real_results.append(tmp_result)
				
				write_sql(real_results)
						
			#for individual_item in item_query_group:	#write to SQL by individual item
			#	
			#	for row_ittr in query_result["emd"]["result"]:
			#		if int(row_ittr["row"]["typeID"]) != int(individual_item):
			#			continue
			#		result_line = [row_ittr["row"]["date"],row_ittr["row"]["regionID"],lookup["types"][row_ittr["row"]["typeID"]],row_ittr["row"]["typeID"],"EMD",row_ittr["row"]["highPrice"],row_ittr["row"]["lowPrice"],row_ittr["row"]["avgPrice"],row_ittr["row"]["volume"],row_ittr["row"]["orders"],None,None]
			#		#print result_line
			#		hold_results.append(result_line)
			#	#print hold_results
			#	#print dates_todo
			#	date_indx=0
			#	previous_entry=hold_results[0] #IF T0 = null, then pass back earliest value to T0
			#	for result_ittr in hold_results:	#Clean up missing values
			#		print result_ittr
			#		print date_indx
			#		if result_ittr[0]== dates_todo[date_indx]:	#found value
			#			real_results.append(result_ittr)
			#			date_indx+=1
			#			previous_entry=result_ittr
			#			continue
			#		else:										#Did not find value, use previous
			#			real_results.append(previous_entry)
			#			date_indx+=1
			#			previous_entry=result_ittr
			#		
			#	write_sql(real_results)
			item_query_group=[]
			display_progress(progress)
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
		tmp_str="REPLACE %s (date,locationID,typeName,typeID,source,priceMax,priceMin,priceAverage,volume,orders,priceOpen,priceClose) VALUES('%s',%s,'%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s);" %(db_name,\
			print_list[0], print_list[1], print_list[2], print_list[3], print_list[4],\
			round(float(print_list[5]),2), round(float(print_list[6]),2), round(float(print_list[7]),2), print_list[8], print_list[9],\
			print_list[10], print_list[11])
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