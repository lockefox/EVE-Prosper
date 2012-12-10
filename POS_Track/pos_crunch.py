#!/Python27/python.exe

from xml.dom.minidom import parse, parseString
import json
import APIhandler

referenceFile = "itemlist.json"
namesFile = "names.json"
#####	GLOBALS	#####
corpAPIs = {
	573031: "gAgo5tcvXm3qwOjg3VFmY0h46CDazOU17RwyozSMw3N3qoleX6gmvwkbw235ipZG"	#HLIB
	}

corpCHAR = {
	573031: 168237945	#cyno moore
	}
	
reference_json = open(referenceFile)
names_json = open (namesFile)

reference = json.load(reference_json)
names = json.load(names_json)


#price{}		#typeID:(buy-price, buy-volume, sell-price, sell-volume)

#def contents (APIfile_assets,uniqueID):
	#Takes unique ID and returns list-of-dict with contents
	# EX: ({"itemID":###,"name"="string","qty":###})

class Module (object):
	#builds module object.  Towers are a collection of MODULE objects
	
	def __init__ (self,uniqueID,typeID):
		self.contents = contents (uniqueID)			#return list of contents
		#self.title = names(uniqueID)				#return unique name (if valid)
		found= False
		for x in reference["root"]["POSequipment"]["POSmods"]:
			if x["typeID"] == typeID:
				self.name = x["name"]
				self.type = x["type"]
				found=True
				
		if found == False:
			self.name="ERROR"
			self.type="ERROR"
			
		self.uniqueID=uniqueID
		self.typeID=typeID
		
		
		
class Tower (object):
	#Set of objects to handle tower information
	#takes a "row" object from 
	detailURL="https://api.eveonline.com/corp/StarbaseDetail.xml.asp"
	def __init__ (self,dom_row,urlcall):
		self.uniqueID=dom_row.getAttribute("itemID")
		self.typeID=dom_row.getAttribute("typeID")
		self.itemname = Module(uniqueID,typeID).name
		self.locationID = dom_row.getAttribute("locationID")
		self.location = reference ["root"]["itemDB"]["systemIDs"][locationID]
		self.moonID = dom_row.getAttribute("moonID")
		temp_state = dom_row.getAttribute("state")
		self.timer=null
		if temp_state == 0:
			self.state = "unanchored"
		elif temp_state == 1:
			self.state = "offline"
		elif temp_state == 2:
			self.state = "onlining"
			self.timer = dom_row.getAttribute("stateTimestamp")
		elif temp_state == 3:
			self.state = "reinforced"
			self.timer = dom_row.getAttribute("stateTimestamp")
		else:
			self.state = "online"
		
			
class Value (object):

	def __init__ (self,typeID):
		self.sell = price[typeID][2]
		self.vol = price[typeID][3]
		self.buy = price[typeID][0]
		self.buyvol = price[typeID][1]
		
	def load(self):		#Queries eve-central and loads market dictionary
		self.derp=1
		
class Moon (object):

	def __init__ (self,uniqueID,typeID,parentID):
		self.derp=1