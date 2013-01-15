#!/Python27/python.exe

from xml.dom.minidom import parse, parseString
import json
#import APIhandler

referenceFile = "itemlist.json"
namesFile = "names.json"
#keysFile= "keys.json"
#####	GLOBALS		#####

##OFFLOAD APIkeys to keys.json
##	DO NOT GIT ADD keys.json.  For project security


	
reference_json = open(referenceFile)
names_json = open (namesFile)

reference = json.load(reference_json)
names = json.load(names_json)

#####	CONTROL		#####


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
	def __init__ (self,dom_row,key,vcode):
		self.uniqueID=dom_row.getAttribute("itemID")
		self.typeID=dom_row.getAttribute("typeID")
		self.itemname = Module(uniqueID,typeID).name
		self.locationID = dom_row.getAttribute("locationID")
		self.location = reference ["root"]["itemDB"]["systemIDs"][locationID]
		self.moonID = dom_row.getAttribute("moonID")
		temp_state = dom_row.getAttribute("state")
		self.timer=None
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
		POSdetails_URL= "%s?KeyID=%s&vCode=%s&itemID=%s" % detailURL,key,vcode,uniqueID
		details_dom = minidom.parse(urllib.urlopen(POSdetails_URL))
		if state == "online":
			for fuelinbay in details_dom.getElementsByTagName('row'):
				item = fuelinbay.getAttribute("typeID")
				for x in reference["root"]["itemDB"]["fuel"]:
					if item == x["itemID"]:
						self.fuelID=item
						self.fuelname=x["name"]
						self.fuelrace=x["race"]
						self.fuel=int(fuelinbay.getAttribute("quantity"))
				if item == "16275":
					self.stront = int(fuelinbay.getAttribute("quantity"))
					
			if stront == None:
				self.stront=0
	
			for fuelbay in reference["root"]["POSequipment"]["TOWERresources"]:
				if fuelbay["itemid"] == typeID:
					self.size = fuelbay["size"]
					self.race = fuelbay["race"]
					self.fuel_baysize = fuelbay["fuelbay"]
					self.stront_baysize = fuelbay["strontbay"]
					self.fueltime = fuel/fuelbay["fuel"]		#returns HOURS fuel remaining
					self.stronttime=stront/fuelbay["stront"]	#returns HOURS stront remaining
	
		else:		#if not online, don't care about fuel/stront values
			self.fuelID=None
			self.fuelname=None
			self.fuelrace=None
			self.fuel=None
			self.stront=None
			self.size = None
			self.race = None
			self.fuel_baysize = None
			self.stront_baysize = None
			self.fueltime = None	#returns HOURS fuel remaining
			self.stronttime=None	#returns HOURS stront remaining
			
	modules = []	#list of Module() objects.  To be loaded by ASSET def

			
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