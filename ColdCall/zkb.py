#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

base_query = conf.get("ZKB","base_query")
query_limit = int(conf.get("ZKB","query_limit"))
subquery_limit = int(conf.get("ZKB","subquery_limit"))
retry_limit = int(conf.get("ZKB","retry_limit"))
default_sleep = int(conf.get("ZKB","default_sleep"))
User_Agent = conf.get("GLOBALS","user_agent")

sleepTime = query_limt/(24*60*60)

valid_modifiers = (
	"kills",
	"losses",
	"w-space",
	"solo",
	"no-items",
	"no-attackers",
	"api-only",
	"xml")
	
class QueryException(Exception):
	def __init__ (self,code):
		self.code = code
	def __str__ (self):
		if self.code == -1:
			return "ZKB requires at least 2 '*ID' identifiers"
		elif self.code == -2:
			mod_list = '\n'.join(valid_modifier)
			return "Invalid query modifier.  Valid Modifiers:\n%s" % mod_list
		elif self.code == -3:
			return "Invalid order modifier.  'asc' or 'desc' only"
		elif self.code == -4:
			return "Invalid ID modifier.  Query limit = %s" % subquery_limit
		elif self.code == -5:
			return "Invalid query modifier type.  Modifier must be base type int"
		else:
			return "Useless generic Exception"
			
class Query(object):
	__initialized = False
	def __init__ (self, queryArgs=""):
		self.address = base_query
		self.queryArgs = queryArgs
		self.queryElements = {}
		self.IDcount = 0
		if queryArgs != "":
			self.IDcount +=2
			#do load into queryElements
		self.__initialized == True
		
	def fetch(self):
		return fetchResults(self)
		
	def orderDirection(self,dir):
		dirLower = dir.lower()
		if dirLower not in ("asc","desc"):
			raise QueryException(-3)
		
		self.queryElements["orderDirection"] = dirLower
	def startTime(self,datevalue):
		validTime = False
		try:
			date = time.strptime(datevalue,"%Y-%m-%d")
		except ValueError as e:
			try:
				date = time.strptime(datevalue,"%Y-%m-%d %H:%M")
			except ValueError as e2:
				try:
					date = time.strptime(datevalue,"%Y%m%d%H%M")
					validTime = True
				except ValueError as e3:
					raise e3
					
		date_str = ""
		if validTime:
			date_str = datevalue
		else:
			date_str = dateConv(date)
		self.queryElements["startTime"] = date_str

	def endTime(self,datevalue):
		validTime = False
		try:
			date = time.strptime(datevalue,"%Y-%m-%d")
		except ValueError as e:
			try:
				date = time.strptime(datevalue,"%Y-%m-%d %H:%M")
			except ValueError as e2:
				try:
					date = time.strptime(datevalue,"%Y%m%d%H%M")
					validTime = True
				except ValueError as e3:
					raise e3
				
		date_str = ""
		if validTime:
			date_str = datevalue
		else:
			date_str = dateConv(date)
			
		self.queryElements["endTime"] = date_str
				
	def dateConv (self,date):
		date_str = date.strftime("%Y%m%d%H%M")
		return date_str
	
	def limit (self,limit):
		if self.singletonValidator(limit):
			self.queryElements["limit"] = limit
		else:
			raise QueryException(-5)
			
	def page (self,page):
		if self.singletonValidator(page):
			self.queryElements["page"] = page
		else:
			raise QueryException(-5)
	
	def year (self,year):
		if self.singletonValidator(year):
			self.queryElements["year"] = year
		else:
			raise QueryException(-5)
			
	def month(self,month):
		if self.singletonValidator(month):
			self.queryElements["month"] = month
		else:
			raise QueryException(-5)
			
	def week (self,week):
		if self.singletonValidator(week):
			self.queryElements["week"] = week
		else:
			raise QueryException(-5)
			
	def beforeKillID (self,killID):
		self.IDcount +=1	
		self.queryElements["beforeKillID"] = self.idValidator(killID)
		
	def afterKillID (self,killID):
		self.IDcount +=1	
		self.queryElements["afterKillID"] = self.idValidator(killID)
		
	def pastSeconds (self,seconds):
		self.IDcount +=1	
		self.queryElements["pastSeconds"] = self.idValidator(seconds)
		
	def characterID (self,characterID):
		self.IDcount +=2	
		self.queryElements["characterID"] = self.idValidator(characterID)
		
	def corpoartionID (self,corporationID):
		self.IDcount +=2	
		self.queryElements["corpoartionID"] = self.idValidator(corporationID)
		
	def allianceID (self,allianceID):
		self.IDcount +=2	
		self.queryElements["allianceID"] = self.idValidator(allianceID)
		
	def factionID (self,factionID):
		self.IDcount +=1	
		self.queryElements["factionID"] = self.idValidator(factionID)
		
	def shipTypeID (self,shipTypeID):
		self.IDcount +=1	
		self.queryElements["shipTypeID"] = self.idValidator(shipTypeID)
		
	def groupID (self,groupID):
		self.IDcount +=1	
		self.queryElements["groupID"] = self.idValidator(groupID)
		
	def solarSystemID (self,solarSystemID):
		self.IDcount +=1
		self.queryElements["solarSystemID"] = self.idValidator(solarSystemID)
		
	def regionID (self,regionID):
		self.IDcount +=1
		self.queryElements["regionID"] = self.idValidator(regionID)
		
	def singletonValidator (self,value):
		valid = False
		if isinstance(value,str):
			if value.isdigit():
				valid = True
		elif isinstance(value,int):
			valid = True
		return valid
		
	def idValidator (self,value):
		returnstr = ""
		if isinstance(value,str):
			tmp_list = value.split(',')
			valid_list = True
			for individual in tmp_list:
				if self.singletonValidator(individual) == False:
					raise QueryException(-5)
					
			returnstr = value
		elif isinstance(value,int):
			returnstr = str(value)
			
		elif type(value) is list:
			valid_list = True
			for individual in value:
				if self.singletonValidator(individual) == False:
					raise QueryException(-5)
					
			returnstr = ','.join(str(x) for x in value)
		return returnstr
		
	def __getattr__ (self,name):	#for modifiers
		mod_str = name.replace('_','-')
		if mod_str not in valid_modifiers:
			raise QueryException(-2)
		
		
		if mod_str in ("w-space","solo"):
			self.IDcount += 1
		
		self.queryElements[str(mod_str)] = True
		
	def __str__ (self):
		if self.IDcount < 2:
			raise QueryException(-1)
		query_modifiers = self.queryArgs
		for key,value in self.queryElements.iteritems():
			if value == True:
				query_modifiers = "%s/%s" % (key,query_modifiers)	#fetch modifiers must be first
			else:
				query_modifiers = "%s%s/%s/" % (query_modifiers,key,value)
				
		return "%s%s" % (self.address,query_modifiers)

def fetchLatestKillID ():
	singleton_query = Query("api-only/solo/kills/limit/1/")
	kill_obj = fetchResults(singleton_query,1)
	
	return kill_obj[0]["killID"]
	
def latestKillID(kill_obj):
	earliest_time = datetime.strptime("1970-01-01 00:00:00","%Y-%m-%d %H:%M:%S")	#epoch 0
	latest_ID = 0
	for kill in kill_obj:
		killTime = datetime.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		if killTime > earliest_time:
			earliest_time = killTime
			latest_ID = kill["killID"]
			
	return latest_ID
	
def earliestKillID(kill_obj):
	latest_time = datetime.utcnow()
	earliest_ID = 0
	for kill in kill_obj:
		killTime = datetime.strptime(kill["killTime"],"%Y-%m-%d %H:%M:%S")
		if killTime < latest_time:
			latest_time = killTime
			earliest_ID = kill["killID"]
			
	return earliest_ID
	
def fetchResults(queryObj,scrapeHeader=0):
	zkb_url = str(queryObj)
	
	request = urllib2.Request(zkb_url)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',User_Agent)
	
	#log query
	
	for tries in range (0,retry_limit):
		time.sleep(sleepTime*(tries+1))
		try:
			opener = urllib2.build_opener()
			header_hold = urllib2.urlopen(request).headers
			raw_zip = opener.open(request)
			dump_zip_stream = raw_zip.read()
		except urllib2.HTTPError as e:
			#log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
			print "retry %s: %s" %(zkb_addr,tries+1)
			continue
		except urllib2.URLError as er:
			#log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), er))
			print "URLError.  Retry %s: %s" %(zkb_addr,tries+1)
			continue
		except socket.error as err:
			#log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), err))
			print "Socket Error.  Retry %s: %s" %(zkb_addr,tries+1)
		_snooze(header_hold)
		
		try:
			dump_IOstream = StringIO.StringIO(dump_zip_stream)
			zipper = gzip.GzipFile(fileobj=dump_IOstream)
			JSON_obj = json.load(zipper)
		except ValueError as errr:
			#log_filehandle.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), errr))
			print "Empty response.  Retry %s: %s" %(zkb_addr,tries+1)
			
		else:
			break
	else:
		print header_hold
		sys.exit(2)
		
	return JSON_obj
	
def _snooze(http_header,multiplier=1):
	global query_limit, sleepTime
	
	try:
		query_limit  = int(http_header["X-Bin-Max-Requests"])
		request_used = int(http_header["X-Bin-Request-Count"])
	except KeyError as e:
		sleepTime = query_limit/(24*60*60)*multiplier
		return sleepTime
	sleepTime = 0
	if request_used/max_request <= 0.5:
		return sleepTime
	elif request_used/max_request > 0.9:
		sleepTime = query_limit/(24*60*60)*multiplier*2
		return sleepTime	
	elif request_used/max_request > 0.75:
		sleepTime = query_limit/(24*60*60)*multiplier
		return sleepTime
	elif request_used/max_request > 0.5:
		sleepTime = query_limit/(24*60*60)*multiplier*0.5
		return sleepTime
	else:
		sleepTime = query_limit/(24*60*60)*multiplier
		return sleepTime
		
def _snoozeSetter(http_header):
	global query_limit,snooze_timer
	
	try:
		query_limit = int(http_header["X-Bin-Max-Requests"])
	except KeyError as e:
		print "WARNING: http_header key 'X-Bin-Max-Requests' not found"
		query_limit = int(conf.get("ZKB","query_limit"))
		snooze_timer = query_limit/(24*60*60)	#requests per day
		
	
def _politeSnooze(http_header):
	global snooze_timer
	call_sleep = 0
	conn_allowance = int(http_header["X-Bin-Attempts-Allowed"])
	conn_reqs_used = int(http_header["X-Bin-Requests"])	
	conn_sleep_time= int(header["X-Bin-Seconds-Between-Request"])
	
	if (conn_reqs_used+1)==conn_allowance:
		time.sleep(conn_sleep_time)

def main():
	newQuery = Query()
	newQuery2 = Query("api-only/characterID/628592330/losses/")
	
	newQuery.api_only
	newQuery.characterID(628592330)
	newQuery.losses
	
	print newQuery
	print newQuery2
	
if __name__ == "__main__":
	main()	