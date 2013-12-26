#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import MySQLdb
import ConfigParser

##Config File Globals##
conf = ConfigParser.ConfigParser()
conf.read(["scraper.ini","scraper_local.ini"])

########## GLOBALS ##########
db_schema=""
db=None
db_cursor=None

class BPO:
	def __init__(self):
		self.name=""
		self.output=""
		self.meta=0
		self.prodtime=0
		self.tech=0
		self.
	
def init():
	global ,db_schema,db,db_cursor
	db_schema=conf.get("GLOBALS" ,"db_name")
	db_IP=conf.get("GLOBALS" ,"db_host")
	db_user=conf.get("GLOBALS" ,"db_user")
	db_pw=conf.get("GLOBALS" ,"db_pw")
	db_port=conf.getint("GLOBALS" ,"db_port")