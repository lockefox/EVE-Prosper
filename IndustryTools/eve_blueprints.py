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
		self.name = ""
		self.base_materials = {}
		self.extra_materials = {}
		self.productionEfficiency = {}
		self.materialEffciency = {}
		self.copying = {}
		self.reverseEngineering = {}
		self.inventionMaterials = {}
		
		
	def load_xml(self,xmlObj):
		test=1
	def load_json(self,jsonObj):
		test=1
		
	def __setattr__(self,name,value):	#magic method to set attribute to match BPO_file
		super(Test,self).__setattr__(name,value)
		
	def __getattr__(self,name):			#magic method to check if __setattr__ misses an entry
		return None		#avoid exceptions?
		
def init():
	tmpBPO_dict = {}
	bpo_file = conf.get("EVE_BLUEPRINTS" ,"BPO_list")
	print "Loading BPO data into memory: %s" % bpo_file
	try:	#parse as XML by default
		minidom.parse(bpo_file)
		tmpBPO_dict = BPO_loader_xml(bpo_file)
	except Exception, e:
		#if not XML, try JSON
		print e
		sys.exit(1)
		
	return tmpBPO_dict
def main():
	global BPO_dict
	BPO_dict = init()

	
if __name__ == "__main__":
	main()