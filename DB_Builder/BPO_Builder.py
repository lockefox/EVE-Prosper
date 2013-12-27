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
default_character = None
skill_dict={}

class Character:
	def __init__(self):
			#remove manual definition?  Do math off skills{}
		self.production_efficiency		=5
		self.industry					=5
		self.advanced_mass_production	=4
		self.mass_production			=5
		self.lab_operations				=5
		self.advanced_lab_operations	=4
		self.science					=5
		self.metalurgy					=5
		self.research					=5
		
		self.research_slots				= self.lab_operations + self.advanced_lab_operations + 1		#10
		self.manufacture_slots			= self.mass_production + self.advanced_mass_production + 1	#10
		self.prod_eff					= (25-(5*self.production_efficiency)) 					#1
		##Add Invention/T3 skills
		self.skills = {}	#hold skills by itemID
	def load_skills(self,API_return):
		#take skills API from eveapi
		test=1
		
class BPO:
	def __init__(self):
		self.typeID		=0
		self.groupID	=0
		self.meta	    =0
		self.outType    =0
		self.tech	    =0
		self.BPOname    =""
		self.parent     =0
		self.mfgtime    =0
		self.PEtime	    =0
		self.MEtime     =0
		self.cpytime    =0
		self.tchtime    =0
		self.prodmod    =0
		self.matmod     =0
		self.waste 	    =0
		self.prodlmt    =0
		
		self.materials	={}
		self.extra_mats	={}

	def bp_type_load(self,cursor_line):		#This is terrible.  You should feel bad
		typeID	= cursor_line[0]
		groupID	= cursor_line[1]
		meta	= cursor_line[2]
		outType	= cursor_line[3]	#Need name lookup
		tech	= cursor_line[4]
		BPOname	= cursor_line[5]
		parent 	= cursor_line[6]	#Need name lookup
		mfgtime	= cursor_line[7]
		PEtime	= cursor_line[8]
		MEtime	= cursor_line[9]
		cpytime	= cursor_line[10]
		tchtime	= cursor_line[11]
		prodmod	= cursor_line[12]
		matmod	= cursor_line[13]
		waste	= cursor_line[14]
		prodlmt	= cursor_line[15]
	
	def materials(self,ME,prod_line_waste=1):
		build_bill = {}
			#ME Equations: http://wiki.eve-id.net/Equations
		if ME<0:
			for base_item,qty in materials.iteritems():
				item_waste = round(qty*(waste/100)*(1-ME))
				item_waste = round(((25-(5*default_character.production_efficiency))/100)*prod_line_waste)
				build_bill[base_item] = item_waste
		else:
			for base_item,qty in materials.iteritems():
				item_waste = round(qty*(waste/100)*(1/(ME + 1)))		
				item_waste = round(((25-(5*default_character.production_efficiency))/100)*prod_line_waste)
				build_bill[base_item] = item_waste
				
	def dump(self):
		dump_dict={}
		dump_dict["BPO_typeID"]		= typeID
		dump_dict["BPO_typeName"]	= BPOname
		dump_dict["BPO_groupID"]	= groupID
		dump_dict["BPO_parent"]		= parent
		dump_dict["BPO_prodlimit"]	= prodlimit
		
		dump_dict["item_meta"]		= meta
		dump_dict["item_typeID"]	= outType
		
		dump_dict["tech_level"]		= tech
		dump_dict["research_ME"]	= MEtime
		dump_dict["research_PE"]	= PEtime
		dump_dict["research_cpy"]	= cpytime
		
		dump_dict["mats_basemats"]	= materials
		dump_dict["mats_extramats"]	= extra_mats
		dump_dict["math_techtime"]	= tchtime
		dump_dict["math_prodmod"]	= prodmod
		dump_dict["math_matmod"]	= matmod
		dump_dict["math_waste"]		= waste
		
		return dump_dict
def init():
	global db_schema,db,db_cursor,default_character,skill_dict
	db_schema=conf.get("GLOBALS" ,"db_name")
	db_IP=conf.get("GLOBALS" ,"db_host")
	db_user=conf.get("GLOBALS" ,"db_user")
	db_pw=conf.get("GLOBALS" ,"db_pw")
	db_port=conf.getint("GLOBALS" ,"db_port")
	
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
		
	db_cursor = db.cursor()
	try:
		db_cursor.execute('''SELECT t.typeID,t.typeName
			FROM invtypes t
			JOIN invgroups grp on (grp.groupID=t.groupID)
			WHERE grp.categoryID=16''')
	except MySQLdb.Error as e:
		print "Unable to execute query on %s: %s" % (db_schema,e)
		sys.exit(-1)
	skill_list_hold = db_cursor.fetchall()
	
	for row in skill_list_hold:
		skill_dict[row[0]]=row[1]
		
	default_character = Character()
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
		tmp_bpo = BPO()
		tmp_bpo.bp_type_load(item)	#push mySQL data into BPO object
		BPO_lookup.append(tmp_bpo)
		


if __name__ == "__main__":
	main()