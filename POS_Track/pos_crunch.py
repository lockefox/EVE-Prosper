#!/Python25/python.exe

from xml.dom.minidom import parse, parseString

#####	GLOBALS	#####
corpAPIs = {
	573031: "gAgo5tcvXm3qwOjg3VFmY0h46CDazOU17RwyozSMw3N3qoleX6gmvwkbw235ipZG"	#HLIB
	}

corpCHAR = {
	573031: 168237945	#cyno moore
	}
	
	
#POSmods = {
POS_tower={
		##CONTROL TOWERS##
	12235: "Amarr Control Tower",
	20059: "Amarr Control Tower Medium",
	20060: "Amarr Control Tower Small",
	16213: "Caldari Control Tower",
	20061: "Caldari Control Tower Medium",
	20062: "Caldari Control Tower Small",
	12236: "Gallente Control Tower",
	20063: "Gallente Control Tower Medium",
	20064: "Gallente Control Tower Small",
	16214: "Minmatar Control Tower",
	20065: "Minmatar Control Tower Medium",
	20066: "Minmatar Control Tower Small",
	}
POS_mfg={
		##MFG ARRAYS##
	24657: "Advanced Large Ship Assembly Array",
	24655: "Advanced Medium Ship Assembly Array",
	24653: "Advanced Small Ship Assembly Array",
	24658: "Ammunition Assembly Array",
	24575: "Capital Ship Assembly Array",
	24660: "Component Assembly Array",
	24659: "Drone Assembly Array",
	13780: "Equipment Assembly Array",
	29613: "Large Ship Assembly Array",
	24654: "Medium Ship Assembly Array",
	16220: "Rapid Equipment Assembly Array", 
	24574: "Small Ship Assembly Array",
	30389: "Subsystem Assembly Array",
	24656: "X-Large Ship Assembly Array",
	}
POS_research={
		##RESEARCH LABS##
	16216: "Mobile Laboratory",
	28351: "Advanced Mobile Laboratory",
	32245: "Hyasyoda Mobile Laboratory",
	25305: "Drug Lab",
	24567: "Experimental Laboratory",	
	}
POS_moon={
		##MOON MINING##
	20175: "Simple Reactor Array",
	16869: "Complex Reactor Array",
	22634: "Medium Biochemical Reactor Array",
	30656: "Polymer Reactor Array",
	16221: "Moon Harvesting Array",
	14343: "Silo",
	25270: "Biochemical Silo",
	25271: "Catalyst Silo",
	17982: "Coupling Array",
	25280: "Hazardous Chemical Silo",
	30655: "Hybrid Polymer Silo",
	}
POS_weapon={
		##WEAPONS##
	17174: "Ion Field Projection Battery",
	17175: "Phase Inversion Battery",
	17176: "Spatial Destabilization Battery",
	17177: "White Noise Generation Battery",
	17178: "Stasis Webification Battery",
	17180: "Sensor Dampening Battery",
	17181: "Warp Disruption Battery",
	17182: "Warp Scrambling Battery",
	17167: "Small Beam Laser Battery",
	17168: "Medium Beam Laser Battery",
	16694: "Large Beam Laser Battery",
	17408: "Small Pulse Laser Battery",
	17407: "Medium Pulse Laser Battery",
	17406: "Large Pulse Laser Battery",
	16222: "Light Missile Battery",
	16695: "Heavy Missile Battery",
	16696: "Cruise Missile Battery",
	16697: "Torpedo Battery",
	17773: "Citadel Torpedo Battery",
	17772: "Small AutoCannon Battery",
	17771: "Medium AutoCannon Battery",
	17772: "Small AutoCannon Battery",
	16631: "Small Artillery Battery",
	16688: "Medium Artillery Battery",
	16689: "Large Artillery Battery",
	16690: "Small Railgun Battery",
	16691: "Medium Railgun Battery",
	16692: "Large Railgun Battery",
	17404: "Small Blaster Battery",
	17403: "Medium Blaster Battery",
	17402: "Large Blaster Battery",
	}
POS_other={
		##OTHER###
	17621: "Corporate Hangar Array",
	27673: "Cynosural Generator Array",
	27674: "Cynosural System Jammer",
	12237: "Ship Maintenance Array",
	24646: "Capital Ship Maintenance Array",
	27897: "Jump Bridge",
	19470: "Intensive Refining Array",
	12239: "Medium Intensive Refining Array",
	12238: "Refining Array"
	}
POS_fuel={
	"Gallente": 4312,
	"Caldari": 4051,
	"Minmatar": 4246,
	"Amarr": 4247
	}
class Module (object):
	
	def __init__ (self,uniqueID,typeID):
		self.contents = {}			#return list of contents
		#self.title = names(uniqueID)	#return unique name (if valid)
		if typeID in POS_tower:
			self.type="tower"
			self.name=POS_tower[typeID]
		elif typeID in POS_weapon:
			self.type="weapon"
			self.name=POS_weapon[typeID]
		elif typeID in POS_moon:
			self.type="moon"
			self.name=POS_moon[typeID]
		elif typeID in POS_research:
			self.type="research"
			self.name=POS_research[typeID]
		elif typeID in POS_mfg:
			self.type="mfg"
			self.name=POS_mfg[typeID]
		elif typeID in POS_other:
			self.type="other"
			self.name=POS_other[typeID]
		else:
			self.type="ERROR"
			self.name="ERROR"
		self.uniqueID=uniqueID
		self.typeID=typeID
		
class Tower (object):
	#Set of objects to handle tower information
	
	def __init__ (self,uniqueID,typeID):
		
		temp_tower = Module(uniqueID,typeID)
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