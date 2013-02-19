#!/Python27/python.exe

#####	DB_BUILDER.PY	#####
#	A wrapper to build the Prosper DB's locally for the purpose of debug
#
#	Coalesses the various DB building tools into one easy script
#	Controlled by "config.ini" file + some limited cmd line args
#
#############################

#####		INITS		#####
import sys,csv, sys, math, os,  subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue
import init, eve_central
#####		GLOBALS		#####


def main():
	print "main"
	datelist = eve_central.datelist(init.startdate,init.enddate)
	
	for date in datelist:
		dumpfile = eve_central.fetch_dump(date)		#CSV object
		orderlist = eve_central.csv_to_orderdict(dumpfile)
		
		sys.exit(1)
			
	
if __name__ == "__main__":
	init.proginit()
	init.parseargs()
	init.dbinit()
	main()