#!/Python27/python.exe
##Try 2.0 for processing dump files for loading SQL file
##Designed for UNIX environment
##For win/DOS, install cygwin: http://www.cygwin.com/
##	CYGWIN + MYSQLDB:
##		--Install all the DB/Python modules for cygwin
##		--run: easy_install mysql-python
##		--Verify with python terminal: import MySQLdb
##Processes raw dump files from eve central: eve-central.com/dumps

import csv, sys, math, os, gzip, getopt, subprocess, math
import MySQLdb
	#NOTES: http://thingsilearned.com/2009/05/03/simple-mysqldb-example/

##	Globals	##
DATABASE_HOST = "127.0.0.1"
DATABASE_USER = "root"
DATABASE_NAME = "eve_marketdata"
DATABASE_PASSWD = "bar"
DATABASE_PORT = "3306"

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
						temp = long(data["volenter"])
						delta = float(data["price"])
						R = delta * long(data["volenter"]) / temp
						M2 = long(data["volenter"]) * delta * R
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = M2
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = M2/long(data["volenter"])
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
					temp = long(data["volenter"])
					delta = float(data["price"])
					R = delta * long(data["volenter"]) / temp
					M2 = long(data["volenter"]) * delta * R
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = M2
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = M2/long(data["volenter"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
			else:
					#initialize totally new key
				cleanlist[data["typeid"]] = {}
				cleanlist[data["typeid"]][data["systemid"]]={}
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
				
					#initialize general data values#
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])	#o/
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
				
					#initialize running-average values#

				temp = long(data["volenter"])
				delta = float(data["price"])
				R = delta * long(data["volenter"]) / temp
				M2 = long(data["volenter"]) * delta * R
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = M2
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = M2/long(data["volenter"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
				
				
		#print output
	#print cleanlist["39"][systemFilter]	#prints whole price object for [type][location]
	
	outlist = list_izer(cleanlist, filezip)
	for line in range(1,15):
		if outlist[line][-1] is "":
			outlist[line][-1]="NULL"
		#cursor.execute("INSERT INTO \'rawdata\' VALUES (%d, %s, %d, %d, %s, %d, %d, %d, %d, NULL)" %/ line) (itemid,order_date,regionID,systemID,order_type,price_max_,price_min,price_avg,price_stdev) 
		cursor.execute( "INSERT INTO rawdata (itemid,order_date,regionID,systemID,order_type,price_max_,price_min,price_avg,price_stdev) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % tuple(outlist[line]))
		#cursor.execute("INSERT INTO rawdata (itemid) VALUE (%s)" % outlist[line][0])
		#print outlist[line]
	rawdump.close()
	
def list_izer(resultList, filepath):
	#takes cleanlist{} and returns a list-list-... array
	#filename needed to parse out date key
	#Used for CSV output (ill advised)
	
		#build Headder
	list_out = []
	header = ["itemid","date","region","system","type","max","min","avg","stdev","other"]
	list_out.append(header)
		#parse date from filename
	(dump,filename) = filepath.split("%s/" % dumpfile)
	(date,dump) = filename.split(".dump")
	
	for itemid,first_dict in resultList.iteritems():
		for system,second_dict in first_dict.iteritems():
			for type,root_dict in second_dict.iteritems():
	
				entry = [itemid,date,root_dict["region"],system,type,root_dict["max"],root_dict["min"],root_dict["avg"],root_dict["stdev"],""]
				list_out.append(entry)
		
	return list_out
	
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
def initDB():
	db = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, port=int(DATABASE_PORT), db=DATABASE_NAME)
	cursor = db.cursor()
	#cursor.exectue("drop database %s; create database %s" % (DATABASE_NAME,DATABASE_NAME) )
	#db = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, port=int(DATABASE_PORT) db=DATABASE_NAME)
	return cursor
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
	cursor=initDB()
	main()
