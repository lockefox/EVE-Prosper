#!/Python27/python.exe
import datetime, json, urllib2,gzip, StringIO
import init
#https://zkillboard.com/information/api/

def tozKBtime(to_convert):
	#takes to_convert as datetime 
	stringtime = to_convert.datetime.strftime("%Y%m$d")
	zKBtime = "/starttime/%s0000/endtime/%s2359" % (stringtime,stringtime)
	return zKBtime
	
def query_range(daterange):
	#takes list of desired dates and returns (starttime,endtime) list of queries
	
	return date_list
	
	
class kills_query(object):
		#query_string=defaultQuery/tozKBtime/groupID/#group
	def __init__(self,query_string):
		self.kill_pages=pageloader
		self.query_string=query_string
		
	def pageloader(self):
		#fetch page1
		zKB_json=zKB_fetch(self.query_string)
		pagecount=1	#start with 
		kills_morepage = False
		#if json_tmp kills count =200, set morepage True
		
		while (kills_morepage):
		#if killID count = 200 (>199)
			page_mod="page/%d" % pagecount
			mod_query = "%s%s" % (self.query_string,page_mod)
			zKB_json_tmp = zKB_fetch (mod_query)
			#if json_tmp kills count =200, set morepage True
		
		
def zKB_fetch(query_string):
	#takes default_path + query_string and returns the parsed JSON object
	base_URL = init.config.get("TOASTER_CFG","query")
	request_URL = "%s%s" % (base_URL,query_string)
		
		#fetch zipped query
	request = urllib2.Request(request_URL)
	request.add_header('Accept-encoding', 'gzip')
	request.add_header('User-Agent','eve-prosper.blogspot.com')	#requested header for zkb: https://zkillboard.com/information/api/
	opener = urllib2.build_opener()
	raw_zip = opener.open(request)
	dump_zip_stream = raw_zip.read()
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	
	JSON_obj = json.load(zipper)
	
	return JSON_obj