import MySQLdb
import ConfigParser

###TODO: single config parser on import?
conf = ConfigParser.ConfigParser()
conf.read(["init_tmp.ini","init.ini"])

def __init__():
	test=1
	
class Blueprint:
	def __init__(self):
		self.typeName = ""
		self.typeID = 0
		self.groupID = 0
		self.productTypeID = 0
		self.productTypeName = ""
		self.productGroupID = 0
		self.productCategory = 0
		self.parentTypeID = 0
		self.parentTypeName = ""
		self.techLevel = 0
		self.defaultRunsT2 = 10
		self.base_materials = []
		##self.extra_materials = [] #NOT NEEDED IN KRONOS
		self.productionEfficiency = []
		self.materialEffciency = []
		self.copying = []
		self.reverseEngineering = []
		self.inventionMaterials = []
		self.intermediateMaterials = {}
		
	def __str__(self):
		return self.typeName
	
	def __int__(self):
		return self.typeID
		
	def billOfMaterials(self,characterObj,ME,materialModifier=1,implantModifier=1):
		