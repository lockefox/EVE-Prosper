#!/Python27/python.exe
import datetime, json, urllib2,gzip, StringIO, getopt, time
import init
#https://zkillboard.com/information/api/

##	TOASTER SPECIFIC File Globals	##
systemlist_json = open("toaster_systemlist.json")
systemlist = json.load(systemlist_json)

shiplist_json = open("toaster_shiplist.json")
shiplist = json.load(shiplist_json)

debug_samplefile = "zkb_example.json"
debug_samplefile_json = open(debug_samplefile)
debug_sample = json.load(debug_samplefile_json)

##	TOASTER Global Variables	##
debug = 0
pause_interval = init.config.get("TOASTER_CFG","pause_interval")
pause_length = init.config.get("TOASTER_CFG","pause_length")
zKB_calls = 0	#counter for number of calls made to zKB up to pause_interval
zKB_calls_tot=0	#counter for number of calls made to zKB total
toaster_strikes = init.strikes("toaster")
def tozKBtime(to_convert):
	#takes to_convert as datetime 
	stringtime = to_convert.datetime.strftime("%Y%m%d")
	zKBtime = "/starttime/%s0000/endtime/%s2359" % (stringtime,stringtime)
	return zKBtime
	
def query_range(date_start, date_end):
	#takes list of desired dates and returns (starttime,endtime) list of queries
	
	return date_list
	
	
class kills_query(object):
		#query_string=defaultQuery/tozKBtime/groupID/#group
	def __init__(self,query_string):
		self.kill_pages=pageloader
		self.query_string=query_string
		self.pagecount=1
		
	def pageloader(self):
		#fetch page1
		zKB_json=zKB_fetch(self.query_string)
		kills_morepage = False
		if len(zKB_json.keys()) == 200:
			kills_morepage=True
		
		while (kills_morepage):
		#if killID count = 200 (>199)
			page_mod="page/%d" % self.pagecount
			mod_query = "%s%s" % (self.query_string,page_mod)
			zKB_json_tmp = zKB_fetch (mod_query)
			if len(zKB_json_tmp.keys()) < 200:
				kills_morepage=False
			self.pagecount += 1
		
		
def zKB_fetch(query_string):
	#takes default_path + query_string and returns the parsed JSON object
	cooling_heels()		#inserts a pause to allow connection to cool (avoid blacklist)
	base_URL = init.config.get("TOASTER_CFG","query")
	request_URL = "%s%s" % (base_URL,query_string)
		
		#fetch zipped query
	request = urllib2.Request(request_URL)
	request.add_header('Accept-encoding', 'gzip')
	request.add_header('User-Agent','eve-prosper.blogspot.com')	#requested header for zkb: https://zkillboard.com/information/api/
	for tries in range (0,init.config.get("GLOBALS"),"retry")+1):
		try
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
		print "Could not fetch %s" % query_string
		toaster_strikes.increment()
		
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	
	return JSON_obj

def cooling_heels():	#Keeps count of zKB API call count and inserts delays to avoid blacklisting
	zKB_calls += 1	
	zKB_calls_tot +=1
	
	if zKB_calls >= pause_interval:
		time.sleep(pause_length)
		zKB_calls =0
		toaster_strikes.decrement()	#lowers strike counter (to avoid collected fails)
	
	
def toast_parseargs():	#For running standalone/debug
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hs:ed",["startdate=","enddate=","debug"])
	except getopt.GetoptError:
		print 'toaster.py -s YYYY-MM-DD'
		sys.exit(2)
		
	for opt, arg in opts:
		if opt == '-h':
			toast_help()
		elif opt in ("-s","--startdate="):
			try:
				datetime.strptime(arg,"%Y-%m-%d")
			except ValueError:
				print "Invalid startdate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
				
			init.startdate=datetime.strptime(arg,"%Y-%m-%d")
		elif opt in ("-e","--enddate"):
			try:
				datetime.strptime(arg,"%Y-%m-%d")
			except ValueError:
				print "Invalid enddate date format.  Expected YYYY-MM-DD"
				sys.exit(2)
				
			init.enddate=datetime.strptime(arg,"%Y-%m-%d")
		elif opt in ("-d","--debug"):
			print "Running toaster.py with debug"
			debug=1
		else:
			help()
	
	print "parsed input args (toaster.py)"
		
def help():
	print """toaster.py
	designed to run both stand-alone and as an importable module
	needs init.py to initialize globals and DB connections
	
OPTIONS:
	-s,--startdate=: YYYY-MM-DD 			default=Cruicible Release (2011-11-29) (DB_Builder default)
	(-e,--enddate=): YYYY-MM-DD 			default=today
	(-d,--debug): enables local debug mode	default=false
"""
	sys.exit(1)
def main():
	print "running toaster.py standalone"
	dates_to_run = query_range(init.startdate, init.enddate)
	
if __name__ == "__main__":		#Allow toaster.py to be run as stand-alone
	init.proginit()
	toast_parseargs()
	init.dbinit()
	main()