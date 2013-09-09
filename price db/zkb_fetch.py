#!/Python27/python.exe

import sys,csv, sys, math, os, getopt, subprocess, math, datetime, time, json
import urllib2
import MySQLdb

systemlist="toaster_systemlist.json"	#system breakdown for destruction binning
lookup_file="lookup.json"				#ID->name conversion list
zkb_base="http://zkillboard.com/"
lookup_json = open(lookup_file)
system_json = open(systemlist)
lookup = json.load(lookup_json)
systems= json.load(system_json)

########## GLOBALS ##########

csv_only=0								#output CSV instead of SQL
sql_init_only=0							#output CSV CREATE file
sql_file="pricedata.sql"

days=1
db_name=""
db_schema=""
db=None
db_cursor=None

def init():
	global db_name,db_schema,db,db_cursor
	db_name="killdata"
	db_schema="sdretribution11"
	db_IP="127.0.0.1"
	db_user="root"
	db_pw="bar"
	db_port=3306
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)

		
	db_cursor = db.cursor()
	
	db_cursor.execute("SHOW TABLES LIKE '%s'" % db_name)
	db_exists = len(db_cursor.fetchall())	#zero if not initialized
	#date,itemID,item_category,item_name,[locationbin]
	db_cols_match=1
	if db_exists:
		db_cursor.execute("SELECT COLUMN_NAME FROM INFORATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s'" % (db_schema,db_name))
		existing_cols = db_cursor.fetchall()
		if (len(existing_cols)-4 != len(systems["systemlist"].keys()): #check if bin count lines up
			print "Number of columns in EXISTING table does not match bins in %s" % systemlist
			print "please manually DROP %s from %s" % db_name,db_schema
			
		for bin,sys_list in systems["systemlist"].itteritems():
			if (bin not in existing_cols):
				db_cols_match=0
				print "%s not found in existing db" % bin
				print "please manually DROP %s from %s" % db_name,db_schema
				sys.exit(2)
	
def main():
	#parseargs()
	init()

	
	
if __name__ == "__main__":
	main()