#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket,six
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
			
class Query():
	def __init__ (self):
		self.address = base_query
		self.queryMods = ""
		self.queryElements = {}
		self.IDcount = 0
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
		

	def __getattr__ (self,name):	#for modifiers
		if name not in valid_modifiers:
			raise QueryException(-2)
		
		if name in ("w-space","solo"):
			self.IDcount += 1
		
		self.queryElements[str(name)] = True
	
	def __setattr__(self,name,value):
		query_str=""
		if name.endswith("ID"):
			self.IDcount += 1
		
			if isinstance(value, six.string_types):	#str
				tmp_list = value.split(',')
				if len tmp_list > subquery_limit:
					raise QueryException(-4)
				
				for testID in tmp_list:
					if testID.isdigit():
						continue
					else:
						raise QueryException(-5)
					
				query_str = value

			elif type(value) is list:	#list
				if len(value) > subquery_limit:
					raise QueryException(-4)
				
				for testID in value:
					if isinstance(testID,int):
						continue
					else:
						raise QueryException(-5)
				
				query_str = ','.join(value)
				
			else:	#int
				query_str = str(value)
				
		else:	#not ID query (year,month,day,page,etc)
			if isinstance(value, six.string_types):
				if value.isdigit():
					query_str = value
				else:
					raise QueryException(-5)
					
			elif type(value) is list:	#list
				raise QueryException(-5)	#probably need a new exception
			elif isinstance(value,int):
				query_str = str(value)
			else:
				raise QueryException(-5)	#probably need a new exception
		self.queryElements[str(name)] = query_str
		
	def __str__ (self):
		if IDcount < 2:
			raise QueryException(-1)
		