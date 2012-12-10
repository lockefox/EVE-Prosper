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

def contents (APIfile_assets,uniqueID):
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
	
	def __init__ (self,uniqueID,typeID):
		
		temp_tower = Module(self,uniqueID,typeID)
		race = temp_tower.name.split(' ',1)
		fuelmod = 1		#to be added: Faction tower modifier
		baymod = 1		#to be added: faction tower modifier
			##Fuel returns
			## stront = remaining : max
		if temp_tower.name.find("Small"):
			self.stront=(math.floor(temp_tower.contents[16275]/(100 * fuelmod)))+" : "+(math.floor((12500 * baymod)/3)/(100 * fuelmod))
			self.fuel = (math.floor(temp_tower.contents[POS_fuel[race]]/(10 * fuelmod)))+" : "+(math.floor((35000 * baymod)/5)/(10 * fuelmod))
		elif temp_tower.name.find("Medium"):
			self.stront=(math.floor(temp_tower.contents[16275]/(200 * fuelmod)))+" : "+(math.floor((25000 * baymod)/3)/(200 * fuelmod))
			self.fuel = (math.floor(temp_tower.contents[POS_fuel[race]]/(20 * fuelmod)))+" : "+(math.floor((70000 * baymod)/5)/(20 * fuelmod))
		else:
			self.stront=(math.floor(temp_tower.contents[16275]/(400 * fuelmod)))+":"+(floor((50000 * baymod)/3)/(300 * fuelmod))
			self.fuel = (math.floor(temp_tower.contents[POS_fuel[race]]/(40 * fuelmod)))+" : "+(math.floor((140000 * baymod)/5)/(40 * fuelmod))
			
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