#!/Python27/python.exe
##Try 2.0 for processing dump files for loading SQL file
##Designed for UNIX environment
##For win/DOS, install cygwin: http://www.cygwin.com/
##Processes raw dump files from eve central: eve-central.com/dumps

import csv, sys, math, os, gzip, getopt, subprocess, math

##	Globals	##
dumpfile = "/central_dumps"
datafile = "2012-01-01.dump"	#default file for debug
outfile = "result.csv"
SQL = 0							#default print = CSV
pwd_raw = os.popen("pwd")
pwd = (pwd_raw.read()).rstrip()
cleanlist = {}
globalist = {}
systemFilter="30000142"

def main():
	
	print "running main"

		#READ LIST OF FILES FROM DUMP FOLDER#
	cmdline = "ls %s%s/*.gz" % (pwd,dumpfile)
	try:
		filelist_raw = subprocess.call(cmdline, shell=True)
	except OSerror:
		subprocess.call("mkdir %s" % dumpfile, shell=True, stdout=subprocess.PIPE)	
	filelist_raw = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE)
	output, err = filelist_raw.communicate()
	filelist = output.split("\n") #returns list of filenames
	filelist.pop()	#Removes extra \n empty value from list
	
	for filezip in filelist:
		rawdump = gzip.open(filezip)
		raw_parse = loadCSV(rawdump)

		#parse file
		for order,data in raw_parse.iteritems():
			buy_or_sell = "sell"
			if int(data["bid"]) == 1:
				buy_or_sell = "buy"
			
			if data["typeid"] in cleanlist:
				if data["systemid"] in cleanlist[data["typeid"]]:
					if buy_or_sell in cleanlist[data["typeid"]][data["systemid"]]:
							#existing entry case
							#general data values
						if float(data["price"]) > cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"]:
							cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"]=float(data["price"])
						if float(data["price"]) < cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"]:
							cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"]=float(data["price"])
							
						temp = cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] + int(data["volenter"])
						delta = float(data["price"]) - cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"]
						R = delta * (int(data["volenter"])/temp)
						
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] += R
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] += (cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] * delta * R)
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] += long(data["volenter"])
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"]/cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"]
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = math.sqrt(cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"])
					else:
						#typeid AND system exist, but not buy/sell key
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
						
							#initialize general data values#
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
						
							#initialize running-average values#
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
				else:
						#typeid exists, but not for this system
					cleanlist[data["typeid"]][data["systemid"]]={}
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
					
						#initialize general data values#
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
					
						#initialize running-average values#
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
			else:
					#initialize totally new key
				cleanlist[data["typeid"]] = {}
				cleanlist[data["typeid"]][data["systemid"]]={}
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
				
					#initialize general data values#
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
				
					#initialize running-average values#
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
				
		#print output
	print cleanlist["34"][systemFilter]
	
def loadCSV(filename):
	#accepts string filename and returns dict-dict object of requested file
	parsed_dump ={}
	CSV = csv.reader(filename)
	fields = CSV.next()
	for row in CSV:
		items = zip(fields, row)	#Strips headder from CSV
		item = {}

		for (name,value) in items:
			item[name] = value.strip()	#assigns values to dict using header as keys
		parsed_dump[item["orderid"]]=item #builds return dict-dict object
		
	return parsed_dump
	#parsed_dump[orderid]={orderid:###,regionid:###,...}
	
def parseargs(argv):
	global dumpfile, datafile,outfile
	print "running parseargs"
	try:
		opts, args = getopt.getopt(argv, "i:d:o:S:h", ["input=","debug=","output=","SQL","help"])
	except getopt.GetoptError:
		usage()
		sys.exit(1)
		
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			print "help"
			usage()
			sys.exit(1)
		elif opt in ('-i', '--input='):
			dumpfile=arg
		elif opt in ('-d', '--debug='):
			datafile=arg
		elif opt in ('-o', '--output='):
			outfile=arg
		elif opt in ('-S', "--SQL"):
			SQL=1
		else:
			usage()
			sys.exit(1)

class Entry (object):
	#stores the various values and running tallies for each vector key
	def __init__ (self,data):	#takes dict.  data from main iterator
		self.min
		self.max
		self.vol
		self.avg
		self.stdev
			
if __name__ == "__main__":
	parseargs(argv=sys.argv)
	main()