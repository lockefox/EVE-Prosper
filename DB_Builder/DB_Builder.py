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
			#separated for debug.  Will wrap once modules are all checked out
			#Final will look like file->proc->out to SQL
		cleaned_orderlist = eve_central.csv_to_orderdict(dumpfile)	#returns cleaned output from CSV: csv_to_orderdict["orderid"]=[//header key:value dict//]
		firstpass = eve_central.orderdict_proc(cleaned_orderlist)	#processes down orderDict to orderlist_proc["system-region-itemid-buy_or_sell"]=[(price,volume),...]
		#secondpass= eve_central.
		#print firstpass
		print "added %s to %s" % (date, init.config.get("EVE_CENTRAL","raw_db"))
		sys.exit(1)
			
	
if __name__ == "__main__":
	init.proginit()
	init.parseargs()
	init.dbinit()
	main()