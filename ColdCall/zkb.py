#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

base_query = conf.get["ZKB","base_query"]
query_limit = conf.get["ZKB","query_limit"]
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

class Query():
	def __init__ (self):
		self.address = base_query
		self.queryMods = ""
	def orderDirection(self,dir):
		dirLower = dir.lower()
		if dirLower not in ("asc","desc"):
			raise QueryException(-3)
		
		self.queryMods = "sorderDirection/%s/%s" % (dirLower,self.queryMods)
		
	def __getattr__ (self,name):	#for modifiers
		if name not in valid_modifiers:
			raise QueryException(-2)
		
		self.address = "%s/%s" % (name,self.queryMods)
	
	def __str__ (self):
		return "%s%s" % (self.base_query,self.queryMods)