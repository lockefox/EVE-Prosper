#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read(["init.ini","tmp_init.ini"])

skillName_to_skillID = {}
skillID_to_skillName = {}

class Character:
	def __init__(self):
		self.skills = {}	#skills[skillID]=skill_level
		self.name = ""
		self.characterID = 0
		self.corporationName = ""
		self.corporationID = 0
		self.isInAlliance = 0
		self.allianceName = None
		self.allianceID = None
		self.API_id = 0
		self.API_vcode = 0
	
	def __str__ (self):
		return self.name
	
	def __int__ (self):
		return self.characterID
		
	def __getattr__ (self,name):	#takes Character.skill_name and returns skill level
		if isinstance(name,str):
			skill_lookup = name.replace('_',' ')
			skill_lookup.title()
			try:
				skill_level = self.skills[skillName_to_skillID[skill_lookup]]
			except KeyError as e:
				raise e
			return skill_level
		else:
			raise TypeError
	
def SDE_loadSkills():
	global skillName_to_skillID,skillID_to_skillName
	skill_json = {}
	
	db_schema = conf.get("GLOBALS" ,"db_name")
	db_IP = conf.get("GLOBALS" ,"db_host")
	db_user = conf.get("GLOBALS" ,"db_user")
	db_pw = conf.get("GLOBALS" ,"db_pw")
	db_port = conf.getint("GLOBALS" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
	db_cursor = db.cursor()
	try:
			#Fetch skills lookup table
		db_cursor.execute('''SELECT conv.typeID,
				conv.typeName,
				attr_conv.attributeName,
				COALESCE(attr.valueInt,attr.valueFloat,0)
			FROM invTypes conv
			LEFT JOIN dgmtypeattributes attr ON (conv.typeID = attr.typeID)
			LEFT JOIN dgmattributeTypes attr_conv ON (attr_conv.attributeID = attr.attributeID)
			LEFT JOIN invGroups grp ON (grp.groupID = conv.groupID)
			WHERE grp.categoryID=16''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)
	skill_list_hold = db_cursor.fetchall()
	skill_json["version"] = db_schema
	for row in skill_list_hold:
		skillID        = row[0]
		skillName      = row[1]
		skillAttribute = row[2]
		skillAttrValue = row[3]
			
		skillName_to_skillID[skillName] = skillID
		skillID_to_skillName[skillID] = skillName
		
		if skillID in skill_json:	#entry exists, add skillAttribute
			skill_json[skillID][skillAttribute] = skillAttrValue
		else:	#need to initialize entry for JSON
			skill_json[skillID] = {}
			skill_json[skillID]["skillID"]      = skillID
			skill_json[skillID]["skillName"]    = skillName
			skill_json[skillID][skillAttribute] = skillAttrValue
	
	JSON_dumper(skill_json,conf.get("EVE_CHARACTERS" ,"skill_list"))
	
def JSON_dumper(json_object,filename):
	json_str = json.dumps(json_object, indent=4, sort_keys=True)
	file = open(filename,'w')
	file.write(json_str)
	
def main():
	SDE_loadSkills()
if __name__ == "__main__":
	main()