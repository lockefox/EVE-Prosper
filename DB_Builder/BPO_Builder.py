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
	def __init__(self,cursor_line):
		self.typeID	= cursor_line[0]
		self.groupID= cursor_line[1]
		self.meta	= cursor_line[2]
		self.outType= cursor_line[3]	#Need name lookup
		self.tech	= cursor_line[4]
		self.BPOname= cursor_line[5]
		self.parent = cursor_line[6]	#Need name lookup
		self.mfgtime= cursor_line[7]
		self.PEtime	= cursor_line[8]
		self.MEtime = cursor_line[9]
		self.cpytime= cursor_line[10]
		self.tchtime= cursor_line[11]
		self.prodmod= cursor_line[12]
		self.matmod = cursor_line[13]
		self.waste 	= cursor_line[14]
		self.prodlmt= cursor_line[15]
	
def init():
	global db_schema,db,db_cursor
	db_schema=conf.get("GLOBALS" ,"db_name")
	db_IP=conf.get("GLOBALS" ,"db_host")
	db_user=conf.get("GLOBALS" ,"db_user")
	db_pw=conf.get("GLOBALS" ,"db_pw")
	db_port=conf.getint("GLOBALS" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
	db_cursor = db.cursor()
	
	print "DB Init: %s connection GOOD" % db_schema
	
def main():
	init()
	BPO_lookup=[]	#list of BPO objects

		#Pull initial BPO data to build to-do list
	db_cursor.execute('''SELECT bpo.blueprintTypeID,
	conv.groupID,
	COALESCE(meta.valueInt,meta.valueFloat,0),
	productTypeID,
	techLevel,
	conv.typeName,
	parentBlueprintTypeID,
	productionTime,
	researchProductivityTime,
	researchMaterialTime,
	researchCopyTime,
	researchTechTime,
	productivityModifier,
	materialModifier,
	wasteFactor,
	maxProductionLimit
		FROM invBluePrintTypes bpo
		JOIN dgmTypeAttributes meta ON (meta.typeID=productTypeID AND meta.attributeID=633)
		JOIN invtypes conv ON (bpo.blueprintTypeID=conv.typeID)
		WHERE conv.published = 1
		AND COALESCE (meta.valueInt,meta.valueFloat,0) IN (0,0.0,5,5.0)''')
	tmp_lookup = db_cursor.fetchall()
	for item in tmp_lookup:
		tmp_bpo = BPO(item)	#push mySQL data into BPO object
		BPO_lookup.append(tmp_bpo)
		


if __name__ == "__main__":
	main()