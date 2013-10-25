#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import ElementTree
import MySQLdb
import ConfigParser

########## INIT VARS ##########
BPO_file = open("jeves.blueprints.xml")
lookup_json = open("lookup.json")
lookup = json.load(lookup_json)
crash_file = "material_bridge_crash.json"
crash_obj={}
BPOs = ElementTree.parse(BPO_file)

#Config File Globals
conf = ConfigParser.ConfigParser()
conf.read(["bridge.ini", "bridge_local.ini"])

########## GLOBALS ##########
regionlist = None	#comma separated list of regions (for EMD history)
systemlist = None	#comma separated list of systems (for EC history)
itemlist = None		#comma separated list of items (default to full list)
csv_only = int(conf.get("GLOBALS","csv_only"))				#output CSV instead of SQL
sql_init_only = int(conf.get("GLOBALS","sql_init_only"))	#output CSV CREATE file


########## DB VARS ##########
db_table = conf.get("MATERIALDESTROYED","db_table")
db_name = conf.get("GLOBALS","db_name")
db_IP = conf.get("GLOBALS","db_host")
db_user = conf.get("GLOBALS","db_user")
db_pw = conf.get("GLOBALS","db_pw")
db_port = int(conf.get("GLOBALS","db_port"))
db_cursor = None
db = None

kill_db_name = conf.get("GLOBALS","db_name")
kill_db_table = conf.get("GLOBALS","emd_table")
kill_db_IP = conf.get("GLOBALS","db_host")
kill_db_user = conf.get("GLOBALS","db_user")
kill_db_pw = conf.get("GLOBALS","db_pw")
kill_db_port = int(conf.get("GLOBALS","db_port"))
kill_db_cursor = None
kill_db = None
