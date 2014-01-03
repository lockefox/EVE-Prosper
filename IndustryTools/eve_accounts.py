#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

import eve_characters
from eveapi import eveapi
#import eveapi


conf = ConfigParser.ConfigParser()
conf.read(["init.ini","tmp_init.ini"])

api_file=conf.get("EVE_ACCOUNTS","api_list")

def fetch_characters(apiID,vCode,dict_of_characters):
	
	return dict_of_characters
	
def fetch_allCharacters(apiFile=api_file):
	character_dict = {}	
	api = eveapi.EVEAPIConnection()
	
	api_todo = json.load(open(apiFile))
	characterIndx = 0
	for api_obj in api_todo:
		#test api/connection
		auth = api.auth(keyID = api_obj["keyID"], vCode = api_obj["vCode"])
		try:
			keyinfo = auth.account.APIKeyInfo()
		except eveapi.Error, e:	#regular eveapi errors
			print e
			sys.exit(1)
		except Exception, e:	#bigger issues (socket errs, fires, earthquakes, floods, dogs and cats living together)
			print "barf:", str(e)
			sys.exit(1)
		
def main():
	test=0
	fetch_allCharacters()
if __name__ == "__main__":
	main()