#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
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
skill_dict = {}

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
		
	def __getattr__ (self,name):
		skill_lookup = name.replace('_',' ')	#parse out the _'s
		skill_lookup.title()					#help align casing
		try:
			skill_level = self.skills[skill_dict[skill_lookup]]
		except KeyError as e:
			raise e
		
		return skill_level
		
class BPO:
	def __init__(self):		#http://stackoverflow.com/questions/1389180/python-automatically-initialize-instance-variables
		self.BPO_properties  = {}
		self.ITEM_properties = {}
		self.materials       = {}
		self.extra_mats      = {}
		
			#debug reference
		self.BPO_typeID    = 0
		self.BPO_typeName  = ""
		self.ITEM_typeID   = 0
		self.ITEM_typeName = ""
		
	def bp_type_load(self,cursor_line):	
		self.BPO_properties["typeID"]     = cursor_line[0]
		self.BPO_properties["groupID"]    = cursor_line[1]
		self.BPO_properties["tech_level"] = cursor_line[4]
		self.BPO_properties["typeName"]   = cursor_line[5]
		self.BPO_properties["parent_BPO"] = cursor_line[6]
		self.BPO_properties["mfgtime"]    = cursor_line[7]
		self.BPO_properties["PEtime"]     = cursor_line[8]
		self.BPO_properties["MEtime"]     = cursor_line[9]
		self.BPO_properties["cpytime"]    = cursor_line[10]
		self.BPO_properties["techtime"]   = cursor_line[11]
		self.BPO_properties["prodmod"]    = cursor_line[12]
		self.BPO_properties["matmod"]	  = cursor_line[13]
		self.BPO_properties["waste"]      = cursor_line[14]
		self.BPO_properties["prodlimit"]  = cursor_line[15]
		                             
		self.ITEM_properties["meta"]      = cursor_line[2]
		self.ITEM_properties["typeID"]    = cursor_line[3]
		self.ITEM_properties["typeName"]  = cursor_line[16]
		self.ITEM_properties["groupID"]   = cursor_line[17]
		self.ITEM_properties["categoryID"]= cursor_line[18]
		
		self.BPO_typeID    = self.BPO_properties["typeID"]
		self.BPO_typeName  = self.BPO_properties["typeName"] 
		self.ITEM_typeID   = self.ITEM_properties["typeID"]
		self.ITEM_typeName = self.ITEM_properties["typeName"]
		
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
def init():
	global db_schema,db,db_cursor,default_character,skill_dict
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
		skill_dict[row[0]] = row[1]
		
	default_character = Character()
	print "DB Init: %s connection GOOD" % db_schema
	
def main():
	init()
	BPO_lookup = []	#list of BPO objects

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
		tmp_bpo = BPO()
		tmp_bpo.bp_type_load(item)	#push mySQL data into BPO object
		BPO_lookup.append(tmp_bpo)
		


if __name__ == "__main__":
	main()