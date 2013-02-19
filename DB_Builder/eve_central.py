#!/Python27/python.exe

import Queue,threading
import gzip
import urllib2
import time,datetime
import MySQLdb
import ConfigParser
import init
import sys,csv, gzip, StringIO


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
	opener = urllib2.build_opener()
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)

	CSV_file  = csv.reader(zipper)
	return CSV_file
	
def csv_to_orderdict(CSV_file):
	#takes CSV_file output from fetch_dump and returns a dict-of-dict
	#returnDict["orderid"]=[//header keys:values//]
	#Eliminates repeated orderid's by updating price
	returnDict={}
	
	fields = CSV_file.next()
	for row in CSV_file:
		items = zip(fields, row)
		item={}
	for (name,value) in items:
			item[name] = value.strip()	#assigns values to dict using header as keys
		if item["orderid"] in returnDict:
				#repeated order case
				#update samples to relevent edge
			if item["price"] < returnDict[item["orderid"]]["price"] and returnDict[item["orderid"]]["bid"] is "1":
					#SELL ORDERS: lowest price matters
				returnDict[item["orderid"]]["price"]=item["price"]	
			elif item["price"] > returnDict[item["orderid"]]["price"] and returnDict[item["orderid"]]["bid"] is "0":
					#BUY ORDERS: highest price maters
				returnDict[item["orderid"]]["price"]=item["price"]	
		else:
			returnDict[item["orderid"]]=item #builds return dict-dict object
	
	return returnDict