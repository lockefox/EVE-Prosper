import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket,re
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

import eve_characters
import eve_accounts

conf = ConfigParser.ConfigParser()
conf.read(["init.ini","tmp_init.ini"])

BPO_dict_byBPO = {}
BPO_dict_byProduct = {}

decryptorInfo = {} #decryptorInfo[decryptorID]={"inventionPropabilityMultiplier":##,"inventionMEModifier":##...}
	#####	1112:	inventionPropabilityMultiplier
	#####	1113:	inventionMEModifier
	#####	1114:	inventionPEModifier
	#####	1124:	inventionMaxRunModifier

class BPO:
	def __init__(self):
		self.typeName = ""
		self.typeID = 0
		self.productTypeID = 0
		self.productTypeName = ""
		self.parentTypeID = 0
		self.parentTypeName = ""
		self.techLevel = 0
		self.base_materials = []
		self.extra_materials = []
		self.productionEfficiency = []
		self.materialEffciency = []
		self.copying = []
		self.reverseEngineering = []
		self.inventionMaterials = []
		self.intermediateMaterials = {} #intermediateMaterials["job type"]={"typeID":typeID,"typeName":typeName..."parentBPOid":parentBPOid}
		
	def load_xml(self,xmlObj):
		test=1
	def load_json(self,jsonObj):
		test=1
		
	def __setattr__(self,name,value):	#magic method to set attribute to match BPO_file
		super(Test,self).__setattr__(name,value)
		
	def __getattr__(self,name):			#magic method to check if __setattr__ misses an entry
		return None		#avoid exceptions?
		
	def billOfMats(self,characterObj,ME,materialMultiplier=1,implantModifier=1):
		materials = {}
		final_materials = {}
		
		#Apply ME level
		for mats_dict in self.base_materials:
			itemID = mats_dict["itemID"]
			base_qty = mats_dict["quantity"]
			
			if ME<0:
				base_qty = math.round(base_qty * (self.wasteFactor/100) * (1/(ME+1)))
			else:
				base_qty = math.round(base_qty * (self.wasteFactor/100) * (1-ME))
			
			materials[itemID] = base_qty
			
		#add extra materials
		for extra_dict in self.extra_materials:
			itemID = extra_dict["itemID"]
			extra_qty = mats_dict["quantity"]
			
			if itemID in materials:
				materials[itemID] += extra_qty
			else:
				materials[itemID] = extra_qty
				
		#figure skill/line/implant waste	
		for itemID,qty in materials.iteritems():
			final_materials[itemID] = math.round(((25-(5 * characterObj.Production_Efficiency)) * qty) * (materialMultiplier * implantModifier))
			
		return final_materials
	def inventionMats(self,characterObj,decryptorID=0):
		encryption_methods = (21790,91791,23087,23121)
		invention_skill1 = 0
		invention_skill2 = 0
		encryption_skill = 0
		invention_mats = {}
		
		#load attributes for :math:
		for inv_dict in self.inventionMaterials:
			if inv_dict["category"] == "skill":
				if inv_dict["typeID"] in encryption_methods:
					encryption_skill = inv_dict["typeID"]
				else:
					if invention_skill1 == 0:
						invention_skill1 = inv_dict["typeID"]
					else:
						invention_skill2 = inv_dict["typeID"]
						
			if inv_dict["category"] == "item":
				invention_mats[inv_dict["typeID"]] = inv_dict["quantity"]
			
	def productionTime(self,characterObj,PE,timeMultiplier=1,implantModifier=1):
		
def init():
	tmpBPO_dict = {}
	lookup_file = conf.get("EVE_BLUEPRINTS","lookup_file")
	try:
		with open (lookup_file):
			pass
	except:
		print "Loading BPO lookup data from SDE: %s" % conf.get("GLOBALS" ,"db_name") 
		_SDE_loadBPOlookup(lookup_file)
	bpo_file = conf.get("EVE_BLUEPRINTS" ,"BPO_list")
	
	_import_BPOlookup(lookup_file)
	print "Loading BPO data into memory: %s" % bpo_file
	try:	#parse as XML by default
		parsed_XML = minidom.parse(bpo_file)
		tmpBPO_dict = _BPO_loader_xml(parsed_XML)
	except Exception, e:
		#if not XML, try JSON
		print e
		sys.exit(1)
		
	return tmpBPO_dict

def _SDE_loadBPOlookup(lookup_file):
	global decryptorInfo
	JSON_out = {}
	db_schema = conf.get("GLOBALS" ,"db_name")
	db_IP = conf.get("GLOBALS" ,"db_host")
	db_user = conf.get("GLOBALS" ,"db_user")
	db_pw = conf.get("GLOBALS" ,"db_pw")
	db_port = conf.getint("GLOBALS" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)		
	db_cursor = db.cursor()
	
	try:
		db_cursor.execute(''' SELECT conv.typeID, 
			conv.typeName,
			GROUP_CONCAT(IF(attr.attributeID = 1112, COALESCE(attr.valueInt, attr.valueFloat,0), NULL)) as `inventionPropabilityMultiplier`,
			GROUP_CONCAT(IF(attr.attributeID = 1113, COALESCE(attr.valueInt, attr.valueFloat,0), NULL)) as `inventionMEModifier`,
			GROUP_CONCAT(IF(attr.attributeID = 1114, COALESCE(attr.valueInt, attr.valueFloat,0), NULL)) as `inventionPEModifier`,
			GROUP_CONCAT(IF(attr.attributeID = 1124, COALESCE(attr.valueInt, attr.valueFloat,0), NULL)) as `inventionMaxRunModifier`
			FROM invTypes conv
			LEFT JOIN dgmtypeattributes attr on attr.typeID = conv.typeID
			WHERE conv.groupID IN (728,729,730,731)
			AND attr.attributeID in (1112,1113,1114,1124)
			GROUP BY conv.typeID''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)	
	decryptor_results = db_cursor.fetchall()
	
	for row in decryptor_results:
		typeID   = row[0]
		typeName = row[1]
		probMod  = row[2]
		MEmod    = row[3]
		PEmod    = row[4]
		runMod   = row[5]
		
		decryptorInfo[typeID] = {}
		decryptorInfo[typeID]["typeID"]   = typeID
		decryptorInfo[typeID]["typeName"] = typeName
		decryptorInfo[typeID]["inventionPropabilityMultiplier"] = probMod
		decryptorInfo[typeID]["inventionMEModifier"] = MEmod
		decryptorInfo[typeID]["inventionPEModifier"] = PEmod
		decryptorInfo[typeID]["inventionMaxRunModifier"] = runMod
	JSON_out["decryptorInfo"] = decryptorInfo
	JSON_dumper(JSON_out,lookup_file)
	
def JSON_dumper(json_object,filename):
	json_str = json.dumps(json_object, indent=4, sort_keys=True)
	file = open(filename,'w')
	file.write(json_str)
	
def _import_BPOlookup(lookup_file):
	global decryptorInfo
	
	json_object = json.load(open(lookup_file))
	
	decryptorInfo = json_object["decryptorInfo"]
	
def _BPO_loader_xml(parsed_XML):
	tmpBPO_dict = {}
	
	for blueprint in parsed_XML.getElementsByTagName("blueprint"):
		BPOobj = BPO()
		
	
	return tmpBPO_dict
def main():
	global BPO_dict
	BPO_dict = init()

	
if __name__ == "__main__":
	main()