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

BPO_dict = {}

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
	def inventionMats(self,characterObj):
		
	def productionTime(self,characterObj,PE,timeMultiplier=1,implantModifier=1):
		
def init():
	tmpBPO_dict = {}
	bpo_file = conf.get("EVE_BLUEPRINTS" ,"BPO_list")
	print "Loading BPO data into memory: %s" % bpo_file
	try:	#parse as XML by default
		parsed_XML = minidom.parse(bpo_file)
		tmpBPO_dict = _BPO_loader_xml(parsed_XML)
	except Exception, e:
		#if not XML, try JSON
		print e
		sys.exit(1)
		
	return tmpBPO_dict
	
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