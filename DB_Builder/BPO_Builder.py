#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

##Config File Globals##
conf = ConfigParser.ConfigParser()
conf.read(["scraper.ini","scraper_local.ini"])

########## GLOBALS ##########
db_schema = ""
db = None
db_cursor = None
default_character = None
skill_dict_byID = {}
skill_dict_byname = {}
t1BPO_to_t2BPO = {}
t2BPO_to_t1BPO = {}
job_types = []
xml_root = ET.Element("root")
xml_file = conf.get("GLOBALS" ,"bpo_file")

json_tree = None
json_file = conf.get("GLOBALS" ,"json_file")
interfaceID_to_decryptorGRP ={
	25554:728,	#occult
	25851:728,
	26603:728,
	25555:731,	#esoteric
	25853:731,
	26599:731,
	25553:729,	#cryptic
	25857:729,
	26597:729,
	25556:730,	#incognito
	25855:730,
	26601:730	
}
interfaceID_to_encryptionSkillID ={
	25554:23087,	
	25851:23087,
	26603:23087,
	25555:21790,
	25853:21790,
	26599:21790,
	25553:21791,
	25857:21791,
	26597:21791,
	25556:23121,
	25855:23121,
	26601:23121,
}
datacoreID_to_researchSkillID ={
	11496:30324,	#Defensive Subsystems Engineering
	20114:30788,	#Propulsion Subsystems Engineering
	20115:30325,	#Engineering Subsystems Engineering
	20116:30326,	#Electronic Subsystems Engineering
	20171:11443,	#Hydromagnetic Physics
	20172:11445,	#Minmatar Starship Engineering
	20410:11450,	#Gallentean Starship Engineering
	20411:11433,	#High Energy Physics
	20412:11441,	#Plasma Physics
	20413:11447,	#Laser Physics
	20414:11455,	#Quantum Physics
	20415:11529,	#Molecular Engineering
	20416:11442,	#Nanite Engineering
	20417:11448,	#Electromagnetic Physics
	20418:11453,	#Electronic Engineering
	20419:11446,	#Graviton Physics
	20420:11449,	#Rocket Science
	20421:11444,	#Amarrian Starship Engineering
	20423:11451,	#Nuclear Physics
	20424:11452,	#Mechanical Engineering
	20425:30327,	#Offensive Subsystems Engineering
	25887:11454,	#Caldari Starship Engineering
}

class Character:
	def __init__(self):
			#remove manual definition?  Do math off skills{}
		self.production_efficiency      = 5
		self.industry                   = 5
		self.advanced_mass_production   = 4
		self.mass_production            = 5
		self.lab_operations             = 5
		self.advanced_lab_operations    = 4
		self.science                    = 5
		self.metalurgy                  = 5
		self.research                   = 5
		
		self.research_slots             = self.lab_operations + self.advanced_lab_operations + 1		#10
		self.manufacture_slots          = self.mass_production + self.advanced_mass_production + 1	#10
		self.prod_eff                   = (25-(5*self.production_efficiency)) 					#1
		##Add Invention/T3 skills
		self.skills = {}	#hold skills by itemID
	def load_skills(self,API_return):
		#take skills API from eveapi
		test=1
		
	def lookup (self,skill_lookup):
		if not isinstance(skill_lookup,(int)):	#if skill is a string
			try:
				skill_level = self.skills[skill_dict_byName[skill_lookup]]
			except KeyError as e:
				raise e
		else:
			try:
				skill_level = self.skills[skill_dict_byID[skill_lookup]]
			except KeyError as e:
				raise e
		return skill_level
		
	def __getattr__ (self,name):
		skill_lookup = name.replace('_',' ')	#parse out the _'s
		skill_lookup.title()					#help align casing
		try:
			skill_level = self.skills[skill_dict_byName[skill_lookup]]
		except KeyError as e:
			raise e
		
		return skill_level
		
class BPO:
	def __init__(self):		#http://stackoverflow.com/questions/1389180/python-automatically-initialize-instance-variables
		self.BPO_properties  = {}
		self.ITEM_properties = {}
		self.materials       = {}
		self.extra_mats      = {}
		self.decryptor_group = 0
		self.inv_base_chance = None
		self.inv_skills      = []
		self.inv_encryption  = 0
		
			#debug reference
		self.BPO_typeID    = 0
		self.BPO_typeName  = ""
		self.ITEM_typeID   = 0
		self.ITEM_typeName = ""
	
	def __str__ (self):
		return_str = "BPO:\t%s\t%s\nITEM:\t%s\t%s" % (self.BPO_typeID,self.BPO_typeName,self.ITEM_typeID,self.ITEM_typeName)
		return return_str
		
	def bp_type_load(self,cursor_line):	
		self.BPO_properties["typeID"]     = cursor_line[0]
		self.BPO_properties["groupID"]    = cursor_line[1]
		self.BPO_properties["tech_level"] = cursor_line[4]
		self.BPO_properties["typeName"]   = cursor_line[5]
		self.BPO_properties["parent_BPO"] = cursor_line[6]		#garbage value
		self.BPO_properties["mfgtime"]    = cursor_line[7]
		self.BPO_properties["PEtime"]     = cursor_line[8]
		self.BPO_properties["MEtime"]     = cursor_line[9]
		self.BPO_properties["cpytime"]    = cursor_line[10]
		self.BPO_properties["techtime"]   = cursor_line[11]
		self.BPO_properties["prodmod"]    = cursor_line[12]
		self.BPO_properties["matmod"]	  = cursor_line[13]
		self.BPO_properties["waste"]      = cursor_line[14]
		self.BPO_properties["prodlimit"]  = cursor_line[15]
		                             
		self.ITEM_properties["meta"]      = int(cursor_line[2])
		self.ITEM_properties["typeID"]    = cursor_line[3]
		self.ITEM_properties["typeName"]  = cursor_line[16]
		self.ITEM_properties["groupID"]   = cursor_line[17]
		self.ITEM_properties["categoryID"]= cursor_line[18]
		
		self.BPO_typeID    = self.BPO_properties["typeID"]
		self.BPO_typeName  = self.BPO_properties["typeName"] 
		self.ITEM_typeID   = self.ITEM_properties["typeID"]
		self.ITEM_typeName = self.ITEM_properties["typeName"]
		
			#Fetch ME-affected materials
		db_cursor.execute('''SElECT materialTypeID,quantity
			FROM invtypematerials
			WHERE typeID=%s''' % self.ITEM_typeID)
		for row in db_cursor.fetchall():
			self.materials[row[0]]=row[1]
			
			#BPO materials "extra materials"
		db_cursor.execute('''SELECT ram.activityID,
				ram.requiredTypeID,
				(ram.quantity*ram.damagePerJob),
				conv2.groupID
			FROM ramtyperequirements ram
			JOIN invtypes conv2 ON (ram.requiredTypeID=conv2.typeID)
			JOIN invgroups grp ON (grp.groupID=conv2.groupID)
			WHERE ram.typeID=%s
			AND grp.categoryID <> 16''' % self.BPO_typeID)
		inventable = 0
		for row in db_cursor.fetchall():
				##row[activity,material,qty_needed,material_category]
			job  = job_types[row[0]]
			mat  = row[1]
			qty  = row[2]
			mat_group    = row[3]
			
			if job == "Invention":
				inventable = 1
				
			if self.extra_mats.get(job) == None:	#if job type is empty, initialize dict
				self.extra_mats[job]={}
				
			self.extra_mats[job][mat] = qty	#this is terrible.  Fix it
			if mat_group == 716:	#Data interface
				self.extra_mats[job][mat] = 0	#To avoid miscalculation on bill-of-mats
				self.decryptor_group = interfaceID_to_decryptorGRP[mat]
				self.inv_encryption  = interfaceID_to_encryptionSkillID[mat]
			
			if mat_group == 333: 	#datacore
				self.inv_skills.append(datacoreID_to_researchSkillID[mat])
				

		if inventable: 
			if (self.ITEM_properties["groupID"] in (419,27) 
					or self.ITEM_properties["typeID"] == 17476): #BS, BC, Covetor
				self.inv_base_chance = 0.20
			elif (self.ITEM_properties["groupID"] in (26,28) 
					or self.ITEM_properties["typeID"] == 17476): #Cruiser, Industrial, Retriever
				self.inv_base_chance = 0.25
			elif (self.ITEM_properties["groupID"] in (25,420,513) #Frigate, Destroyer, Freighter, Skiff
					or self.ITEM_properties["typeID"] == 17480):
				self.inv_base_chance = 0.30
			else:
				self.inv_base_chance = 0.40
				
		if self.BPO_properties["groupID"] in (971,990,991,992,993,997):	#T3 parts
				if   self.BPO_properties["typeID"] in (30187,30599,30628,30582,30614,30752):	#Intact parts	
					self.inv_base_chance = 0.40
				elif self.BPO_properties["typeID"] in (30558,30600,30632,30586,30615,30753):	#Malfunctioning parts
					self.inv_base_chance = 0.30
				else: #Wrecked parts
					self.inv_base_chance = 0.20
		
		if self.BPO_properties["tech_level"] == 2:
			try:
				self.BPO_properties["parent_BPO"] = t2BPO_to_t1BPO[self.BPO_properties["typeID"]]
			except KeyError as e:
				self.BPO_properties["parent_BPO"] = None	#Unpublished item handler
				#print self.BPO_properties["typeName"]
				
		elif self.BPO_properties["tech_level"] == 3:
			if self.ITEM_properties["groupID"] == 963:		#T3 Hull
				self.BPO_properties["parent_BPO"] = 997		#hull section group
			elif self.ITEM_properties["groupID"] == 954:	#Defensive Subsystem
				self.BPO_properties["parent_BPO"] = 993
			elif self.ITEM_properties["groupID"] == 955:	#Electronic Subsystem
				self.BPO_properties["parent_BPO"] = 990
			elif self.ITEM_properties["groupID"] == 956:	#Offensive Subsystem
				self.BPO_properties["parent_BPO"] = 991
			elif self.ITEM_properties["groupID"] == 957:	#Propulsion Subsystem
				self.BPO_properties["parent_BPO"] = 971
			elif self.ITEM_properties["groupID"] == 958:	#Engineering Subsystems
				self.BPO_properties["parent_BPO"] = 992
			else:
				self.BPO_properties["parent_BPO"] = None
		else:		
			try:
				self.BPO_properties["parent_BPO"] = t1BPO_to_t2BPO[self.BPO_properties["typeID"]]
			except KeyError as e:
				self.BPO_properties["parent_BPO"] = None	#Unpublished item handler
				#print self.BPO_properties["typeName"]
				
	def bill_of_mats(self,ME,prod_line_waste=1):
		build_bill = {}
			#ME Equations: http://wiki.eve-id.net/Equations
		if ME<0:
			for base_item,qty in materials.iteritems():
				item_waste = round(qty*(self.BPO_properties["waste"]/100)*(1-ME))
				#item_waste = round(((25-(5*default_character.production_efficiency))/100)*prod_line_waste)
				build_bill[base_item] = item_waste
		else:
			for base_item,qty in materials.iteritems():
				item_waste = round(qty*(self.BPO_properties["waste"]/100)*(1/(ME + 1)))		
				#item_waste = round(((25-(5*default_character.production_efficiency))/100)*prod_line_waste)
				build_bill[base_item] = item_waste
			
	def dump(self):
		dump_dict={}
		dump_dict["BPO_properties"]  = self.BPO_properties
		dump_dict["ITEM_properties"] = self.ITEM_properties
		dump_dict["base_materials"]  = self.materials
		dump_dict["extra_materials"] = self.extra_mats
		
		return dump_dict
	##Add __str__ method?	
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")	
def init():
	global db_schema,db,db_cursor	#DB utilities
	global default_character		#character data
	global skill_dict_byID,skill_dict_byname,job_types,t1BPO_to_t2BPO,t2BPO_to_t1BPO	#lookup/translation data

	db_schema = conf.get("GLOBALS" ,"db_name")
	db_IP = conf.get("GLOBALS" ,"db_host")
	db_user = conf.get("GLOBALS" ,"db_user")
	db_pw = conf.get("GLOBALS" ,"db_pw")
	db_port = conf.getint("GLOBALS" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
	db_cursor = db.cursor()
	try:
			#Fetch skills lookup table
		db_cursor.execute('''SELECT t.typeID,t.typeName
			FROM invtypes t
			JOIN invgroups grp on (grp.groupID=t.groupID)
			WHERE grp.categoryID=16''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)
	skill_list_hold = db_cursor.fetchall()	
	for row in skill_list_hold:
		skill_dict_byID[row[0]] = row[1]
		skill_dict_byname[row[1]] = row[0]
	
	try:
		db_cursor.execute('''SELECT activityName
			FROM ramactivities
			ORDER BY activityID ASC''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)
	job_type_hold = db_cursor.fetchall()
	for row in job_type_hold:
		job_types.append(row[0])	
	
	try:
		#https://neweden-dev.com/EVE_Manufacturing_SQL#T1_to_T2_Blueprint_Mapping
		db_cursor.execute('''SELECT it2.typeid basebpid,
				it4.typeid t2bpid
			FROM invTypes it1
			JOIN invBlueprintTypes ibt1 ON it1.typeid=ibt1.producttypeid
			JOIN invTypes it2 ON it2.typeid=ibt1.blueprinttypeid
			JOIN invMetaTypes imt ON imt.parenttypeid=it1.typeid
			JOIN invTypes it3 ON imt.typeid=it3.typeid
			JOIN invBlueprintTypes ibt2 ON it3.typeid=ibt2.producttypeid
			JOIN invTypes it4 ON it4.typeid=ibt2.blueprinttypeid
			WHERE imt.metaGroupID=2''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)
	BPO_match_hold = db_cursor.fetchall()
	for row in BPO_match_hold:
		t1BPO_to_t2BPO[row[0]]=row[1]
		t2BPO_to_t1BPO[row[1]]=row[0]
	
	default_character = Character()
	print "DB Init: %s connection GOOD" % db_schema

def XML_builder (BPO_obj, dict_of_BPOs):
	global xml_root

	blueprint = ET.SubElement(xml_root,"blueprint")
	#blueprint element set
	blueprint.set("BPO_typeName",BPO_obj.BPO_properties["typeName"])
	blueprint.set("BPO_typeID",str(BPO_obj.BPO_properties["typeID"]))
	blueprint.set("BPO_groupID",str(BPO_obj.BPO_properties["groupID"]))
	blueprint.set("BPO_parent",str(BPO_obj.BPO_properties["parent_BPO"]))
	blueprint.set("ITEM_typeName",BPO_obj.ITEM_properties["typeName"])
	blueprint.set("ITEM_typeID",str(BPO_obj.ITEM_properties["typeID"]))
	blueprint.set("ITEM_categoryID",str(BPO_obj.ITEM_properties["categoryID"]))
	blueprint.set("ITEM_groupID",str(BPO_obj.ITEM_properties["groupID"]))
	
	properties = ET.SubElement(blueprint,"properties")
	#blueprint properites
	researchMaterialTime = ET.SubElement(properties,"researchMaterialTime")
	researchProductivityTime = ET.SubElement(properties,"researchProductivityTime")
	researchCopyTime = ET.SubElement(properties,"researchCopyTime")
	productionTime = ET.SubElement(properties,"productionTime")
	techLevel = ET.SubElement(properties,"techLevel")
	productivityModifier = ET.SubElement(properties,"productivityModifier")
	materialModifier = ET.SubElement(properties,"materialModifier")
	wasteFactor = ET.SubElement(properties,"wasteFactor")
	maxProductionLimit = ET.SubElement(properties,"maxProductionLimit")
	baseInventionProbability = ET.SubElement(properties,"baseInventionProbability")
	
	researchMaterialTime.text		= str(BPO_obj.BPO_properties["MEtime"])
	researchProductivityTime.text	= str(BPO_obj.BPO_properties["PEtime"]) 
	researchCopyTime.text			= str(BPO_obj.BPO_properties["cpytime"])     
	productionTime.text				= str(BPO_obj.BPO_properties["mfgtime"])    
	techLevel.text					= str(BPO_obj.BPO_properties["tech_level"])
	productivityModifier.text		= str(BPO_obj.BPO_properties["prodmod"]) 
	materialModifier.text			= str(BPO_obj.BPO_properties["matmod"])    
	wasteFactor.text				= str(BPO_obj.BPO_properties["waste"])     
	maxProductionLimit.text			= str(BPO_obj.BPO_properties["prodlimit"])
	
	if BPO_obj.BPO_properties["tech_level"] == 2:

		try:
			t2BPO_lookup = t2BPO_to_t1BPO[BPO_obj.BPO_properties["typeID"]]
			t2BPO_obj = dict_of_BPOs[t2BPO_lookup]
			t2BPO_chanceStr = str(t2BPO_obj.inv_base_chance)
		except KeyError as e:
			t2BPO_chanceStr = str(None)
			
		baseInventionProbability.text = t2BPO_chanceStr
	else:
		baseInventionProbability.text = str(BPO_obj.inv_base_chance)
def main():
	init()
	BPO_lookup = {}	#list of BPO objects
	BPO_to_product = {}
	product_to_BPO = {}
	XML_FILE_HANDLE = open (xml_file,'w')
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
			maxProductionLimit,
			conv2.typeName,
			conv2.groupID,
			grp.categoryID
		FROM invBluePrintTypes bpo
		JOIN dgmTypeAttributes meta ON (meta.typeID = productTypeID AND meta.attributeID = 633)
		JOIN invtypes conv ON (bpo.blueprintTypeID = conv.typeID)
		JOIN invtypes conv2 ON (bpo.productTypeID = conv2.typeID)
		JOIN invgroups grp ON (grp.groupID = conv2.groupID)
		WHERE conv.published = 1
		AND COALESCE (meta.valueInt,meta.valueFloat,0) IN (0,0.0,5,5.0)''')
	tmp_lookup = db_cursor.fetchall()
	for item in tmp_lookup:
		tmp_dump= {}
		tmp_bpo = BPO()
		tmp_bpo.bp_type_load(item)	#push mySQL data into BPO object
		BPO_lookup[tmp_bpo.BPO_typeID]=tmp_bpo
		tmp_dump = tmp_bpo.dump()
		
		BPO_to_product[tmp_bpo.BPO_typeID]=tmp_bpo.ITEM_typeID
		product_to_BPO[tmp_bpo.ITEM_typeID]=tmp_bpo.BPO_typeID
	#test_bpo_obj = BPO_lookup[18055]
	#print test_bpo_obj.dump()
	print "writing XML"
	for BPO_typeID,bpo_obj in BPO_lookup.iteritems():
		#print BPO_lookup
		#sys.exit()
		XML_builder(bpo_obj,BPO_lookup)
	
	
	#xml_minidom = minidom.parse(ET.dump(xml_root))
	#pretty_xml = xml_minidom.toprettyxml()
	pretty_xml = prettify(xml_root)
	XML_FILE_HANDLE.write(pretty_xml)
	
	#xml_tree = ET.ElementTree(xml_root)
	#xml_tree.write(xml_file)
	
if __name__ == "__main__":
	main()