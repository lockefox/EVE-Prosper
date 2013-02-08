#!/Python27/python.exe

import Queue,threading
import urllib2
import date,datetime
import MySQLdb
import ConfigParser
import init


def datelist(startdate,enddate,cursor):
	#takes startdate/enddate and checks against the existing db to populate a list of missing dates
	list_of_dates=[]
	mindate = enddate
	source_db = config.get("EVE_CENTRAL","datesource")
		#Write a list of ALL DAYS possible
	while mindate != startdate:
		list_of_dates.append(mindate.strftime("%Y-%m-%d"))	#Write string representation of datetime to list
		mindate += datetime.timedelta(days=1)
		
		#remove existing elements
	existing_set
	return list_of_dates