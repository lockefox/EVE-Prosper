#!/Python27/python.exe
##Try 2.0 for processing dump files for loading SQL file
##Designed for UNIX environment
##For win/DOS, install cygwin: http://www.cygwin.com/

import csv, sys, math, os, gzip

##	Globals	##
dumpfile = "/central_dumps"
datafile = "2012-01-01.dump"	#default file for debug
pwd_raw = os.popen("pwd")
pwd = pwd_raw.read()

def main():
	parseargs()
	filepath = "%s/%s" % (pwd,dumpfile)
	
	
def loadCSV(filename):
	#accepts string filename and returns dict-dict object of requested file
	parsed_dump ={}
	CSV = csv.reader(open(filename)):
	fields = data.next()
	for row in CSV:
		items = zip(fields, row)	#Strips headder from CSV
		item = {}

		for (name,value) in items:
			item[name] = value.strip()	#assigns values to dict using header as keys
		parsed_dump[item["orderid"]]=item #builds return dict-dict object
		
	return parsed_dump
	#parsed_dump[orderid]={orderid:###,regionid:###,...}
	
def parseargs():
	global dumpfile, datafile
	
if __name__ == "__main__":
	main()