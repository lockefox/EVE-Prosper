#!/Python27/python.exe

import Queue,threading
import urllib2
import time,datetime
import MySQLdb
import ConfigParser
import init


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