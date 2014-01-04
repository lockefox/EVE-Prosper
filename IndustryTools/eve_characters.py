#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

from eveapi import eveapi

conf = ConfigParser.ConfigParser()
conf.read(["init.ini","tmp_init.ini"])

skillName_to_skillID = {}
skillID_to_skillName = {}
skill_list_default = {}

default_character_xml = conf.get("EVE_CHARACTERS" ,"default_character")

class Character:
	def __init__(self):
		self.skills = skill_list_default	#skills[skillID]=skill_level
		self.name = ""
		self.characterID = 0
		self.corporationName = ""
		self.corporationID = 0
		self.isInAlliance = 0
		self.allianceName = None
		self.allianceID = None
		self.API_id = 0
		self.API_vcode = 0
		self.default_character = 0
	
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
	def dump_skills(self):
		return self.skills
	
	def file_dump(self,filename):		#move to its own function?
		if self.default_character==1:
			return	#no need to print if character is default
		
		xml_root = ET.Element("eveapi")
		result = ET.SubElement(xml_root,"result")
		ET.SubElement(result,"name").text = self.name
		ET.SubElement(result,"characterID").text = str(self.characterID)
		ET.SubElement(result,"corporationName").text = self.corporationName
		ET.SubElement(result,"corporationID").text = str(self.corporationID)
		ET.SubElement(result,"allianceName").text = str(self.allianceName)
		ET.SubElement(result,"allianceID").text = str(self.allianceID)
		
		skill_rowset = ET.SubElement(result,"rowset")
		skill_rowset.set("name","skills")
		skill_rowset.set("key","typeID")
		skill_rowset.set("columns","typeID,level,skillpoints,published,typeName")
		for skill,level in self.skills.iteritems():
			row = ET.SubElement(skill_rowset,"row")
			row.set("typeID",skill)
			row.set("level",level)
			row.set("skillpoints","0")	#dumping SP data on read, not important for math
			row.set("published","1")	#not important for validity
			row.set("typeName",skillID_to_skillName[skill])	#not in official API, but useful for debug
			
		
		ET.SubElement(result,"cachedUntil").text = ""
		
		xmlStr = XML_prettify(xml_root)
		file_writer = open(filename,'w')
		file_writer.write(xmlStr)
	
	def load_eveapi(self,eveapiObj):
		#print eveapiObj
		self.name = eveapiObj.name
		self.characterID = eveapiObj.characterID
		self.corporationName = eveapiObj.corporationName
		self.corporationID = eveapiObj.corporationID
		self.allianceName = eveapiObj.allianceName
		self.allianceID = eveapiObj.allianceID
		
		for row in eveapiObj.skills:
			self.skills[str(row.typeID)] = int(row.level)
			#ignoring sp/published values
			
	def load_default(self,char_xml=default_character_xml):
		domObj = minidom.parse(char_xml)
		rowsets = domObj.getElementsByTagName("rowset")
		for row in rowsets[0].getElementsByTagName("row"):
			self.skills[row.getAttribute("typeID")] = int(row.getAttribute("level"))
		
		self.name = domObj.getElementsByTagName("name")[0].firstChild.nodeValue
		self.characterID = domObj.getElementsByTagName("characterID")[0].firstChild.nodeValue
		self.corporationName = domObj.getElementsByTagName("corporationName")[0].firstChild.nodeValue
		self.corporationID = domObj.getElementsByTagName("corporationID")[0].firstChild.nodeValue
		try:	#value is empty for no alliance
			self.allianceName = domObj.getElementsByTagName("allianceName")[0].firstChild.nodeValue
		except AttributeError as e:
			self.allianceName = None
		self.allianceID = domObj.getElementsByTagName("allianceID")[0].firstChild.nodeValue
		
		self.default_character=1


def XML_prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")	
		
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
				COALESCE(attr.valueInt,attr.valueFloat,0),
				grp.groupID,
				grp.groupName
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
		skillGroupID   = row[4]
		skillGroupName = row[5]
			
		skillName_to_skillID[skillName] = skillID
		skillID_to_skillName[skillID] = skillName
		
		if skillID in skill_json:	#entry exists, add skillAttribute
			skill_json[skillID][skillAttribute] = skillAttrValue
		else:	#need to initialize entry for JSON
			skill_json[skillID] = {}
			skill_json[skillID]["typeID"]       = skillID
			skill_json[skillID]["typeName"]     = skillName
			skill_json[skillID][skillAttribute] = skillAttrValue
			skill_json[skillID]["groupID"]      = skillGroupID
			skill_json[skillID]["groupName"]    = skillGroupName
	
	JSON_dumper(skill_json,conf.get("EVE_CHARACTERS" ,"skill_list"))
	
def JSON_dumper(json_object,filename):
	json_str = json.dumps(json_object, indent=4, sort_keys=True)
	file = open(filename,'w')
	file.write(json_str)

def init():
	global skill_list_default, skillName_to_skillID, skillID_to_skillName
	skill_list_file = conf.get("EVE_CHARACTERS" ,"skill_list")
	#test if skill_list exists
	try:
		with open (skill_list_file):
			pass
	except IOError:
		#skill list doesn't exist
		SDE_loadSkills()
	
	skills_list = json.load(open(skill_list_file))
	#make sure skill list version matches expected SDE
	if skills_list["version"] != conf.get("GLOBALS" ,"db_name"):
		SDE_loadSkills()
		skills_list = json.load(open(skill_list_file))	#reload object
	
	#load module globals for lookups and init
	for skillID,attributes in skills_list.iteritems():
		if skillID == "version":
			continue
		skillName = attributes["typeName"]
		skillID   = str(attributes["typeID"])
		
		skillName_to_skillID[skillName] = skillID
		skillID_to_skillName[skillID] = skillName
		skill_list_default[skillID] = 0
		
def main():
	init()
	default_char = Character()
	default_char.load_default()
	print default_char.name
	
if __name__ == "__main__":
	main()