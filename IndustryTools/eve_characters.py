#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

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
	db_schema = conf.get("GLOBALS" ,"db_name")
	db_IP = conf.get("GLOBALS" ,"db_host")
	db_user = conf.get("GLOBALS" ,"db_user")
	db_pw = conf.get("GLOBALS" ,"db_pw")
	db_port = conf.getint("GLOBALS" ,"db_port")