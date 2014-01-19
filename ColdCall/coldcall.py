#!/Python27/python.exe

import sys, gzip, StringIO, sys, math, os, getopt, time, json, socket
import urllib2
import MySQLdb
import ConfigParser
from datetime import datetime

from eveapi import eveapi
import zkb

#import webapp2
#from google.appengine.ext import ndb
##need appengine SDK: https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python
conf = ConfigParser.ConfigParser()
conf.read(["init.ini", "init_local.ini"])

cursor_participants = None
cursor_fits = None

db_schema = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))
db_participants = conf.get("COLDCALL","db_participants")
db_fits = conf.get("COLDCALL","db_fits")

def main():
	test=1
	
if __name__ == "__main__":
	main()