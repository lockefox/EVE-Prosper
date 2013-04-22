#!/Python27/python.exe

import Queue,threading
import gzip
import urllib2
import time,datetime
import MySQLdb
import ConfigParser
import init
import sys,csv, gzip, StringIO

#strike_limit = init.config.get("GLOBALS","strikes")
#strikes = 0;
eve_central_strikes = init.strikes("eve_central")

def datelist(start_date,end_date):
	#takes startdate/enddate and checks against the existing db to populate a list of missing dates
	list_of_dates=[]
	mindate = start_date #datetime.datetime.strptime(start_date,"%Y-%m-%d")
	tmp_cur = init.cursor
	source_db = init.config.get("EVE_CENTRAL","datesource")
		#Write a list of ALL DAYS possible
	while mindate < end_date:
		list_of_dates.append(mindate.strftime("%Y-%m-%d"))	#Write string representation of datetime to list
		mindate += datetime.timedelta(days=1)
	
		#remove existing elements
	tmp_cur.execute ("SELECT order_date FROM %s" % source_db)
	existing_values = init.cursor.fetchall()
	
	for (rownum,exist_date) in existing_values:
		if exist_date in list_of_dates:
			list_of_dates.remove(exist_date)
	
	return list_of_dates
	
def fetch_dump(date):
	this_year = datetime.datetime.now().year
	date_in = datetime.datetime.strptime(date,"%Y-%m-%d")
	basepath = init.config.get("EVE_CENTRAL","central_path")
	dump_url =""
	CSV_file=None
	
	if date_in.year < this_year:
		dump_url="%s%d/%s.dump.gz" % (basepath,date_in.year,date)
	else:
		dump_url="%s%d/%s.dump.gz" % (basepath,date)
	
		#http://www.diveintopython.net/http_web_services/gzip_compression.html
request = urllib2.Request(dump_url)
request.add_header('Accept-encoding', 'gzip')
for tries in range(0,init.config.get("GLOBALS","retry")+1):	#tries several 
	try:
		opener = urllib2.build_opener()
	except HTTPError as e:
		time.sleep(init.config.get("GLOBALS","retry_wait"))
		continue
	except URLError as er:
		time.sleep(init.config.get("GLOBALS","retry_wait"))
		continue
	else:
		break
else:
	print "Could not fetch %s" % (date)
	//place query back in queue//
	//fail mode//
		eve_central_strikes.increment()	#allows for number of fails, retry later
		
		
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)

	CSV_file  = csv.reader(zipper)
	return CSV_file
	
def csv_to_orderdict(CSV_file):
	#FIRST PASS PROCESSING
	#takes CSV_file output from fetch_dump and returns a dict-of-dict
	#returnDict["orderid"]=[//header keys:values//]
	#Eliminates repeated orderid's by updating price
	parsed_dump={}
	
	fields = CSV_file.next()
	for row in CSV_file:
		items = zip(fields, row)
		item={}
		for (name,value) in items:
			item[name] = value.strip()	#assigns values to dict using header as keys
		if item["orderid"] in parsed_dump:
				#repeated order case
				#update samples to relevent edge
			if item["price"] < parsed_dump[item["orderid"]]["price"] and parsed_dump[item["orderid"]]["bid"] is "1":
					#SELL ORDERS: lowest price matters
				parsed_dump[item["orderid"]]["price"]=item["price"]	
			elif item["price"] > parsed_dump[item["orderid"]]["price"] and parsed_dump[item["orderid"]]["bid"] is "0":
					#BUY ORDERS: highest price maters
				parsed_dump[item["orderid"]]["price"]=item["price"]	
		else:
			parsed_dump[item["orderid"]]=item #builds return dict-dict object
	
	return parsed_dump

def orderdict_proc(parsed_dump):
	#SECOND PASS PROCESSING
	#Processes down individual orders into sorted bins
	tmp=0
	second_pass={}
	
	for order,data in parsed_dump.iteritems():
		buy_or_sell = "buy"
		if data["bid"] is "1":
			buy_or_sell="sell"
		
		entry_string = "%s:%s:%s:%s" % (data["systemid"],data["regionid"],data["typeid"],buy_or_sell)
		#system:region:typeid:buy_or_sell

		if entry_string in second_pass:
				#existing entry case
			second_pass[entry_string].append([data["price"],data["volenter"]])
		else:
				#new entry case
			second_pass[entry_string]=[]
			second_pass[entry_string].append([data["price"],data["volenter"]])
	
	#print second_pass["30000142:10000002:34:sell"]
	return second_pass
	
def wiskerbuilder(entry_list):
	#THIRD PASS PROCESSING
	#Reduces weighted price lists to what is expected to go out to SQL
	#Reduces inputs to max, min, avg, stdev, top-5, bottom-5
	tmp=0