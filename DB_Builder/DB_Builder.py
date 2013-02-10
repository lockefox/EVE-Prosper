#!/Python27/python.exe

#####	DB_BUILDER.PY	#####
#	A wrapper to build the Prosper DB's locally for the purpose of debug
#
#	Coalesses the various DB building tools into one easy script
#	Controlled by "config.ini" file + some limited cmd line args
#
#############################

#####		INITS		#####
import sys,csv, sys, math, os, gzip, getopt, subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue
import init, eve_central
#####		GLOBALS		#####


def main():
	print "main"
	datelist = eve_central.datelist(init.startdate,init.enddate)
	
	
if __name__ == "__main__":
	init.proginit()
	init.parseargs()
	init.dbinit()
	main()