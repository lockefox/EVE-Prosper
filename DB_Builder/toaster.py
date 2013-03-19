#!/Python27/python.exe
import datetime, json
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
		pagecount=0	#start with 
		
		#if killID count = 200 (>199)
		
		#query new pages until count <200
		
		
def zKB_fetch(query_string):
	#takes default_path + query_string and returns the parsed JSON object