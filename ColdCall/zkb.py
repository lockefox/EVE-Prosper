#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

base_query = conf.get("ZKB","base_query")
subquery_limit = conf.get("ZKB","subquery_limit")
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