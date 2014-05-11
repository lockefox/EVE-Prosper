import MySQLdb
import ConfigParser
import eveapi
###TODO: single config parser on import?
conf = ConfigParser.ConfigParser()
conf.read(["init_tmp.ini","init.ini"])

skillName_to_ID = {}
skillID_to_Name = {}
skill_list_default = {}

default_character = None #TODO: build default character.  XML?
default_characterObj = None #todo: slurp in default character once only

class Character():
	def __init__(self):
		self.skills = skill_list_default	#skills={typeID:level,typeID:level}
		self.name = ""
		self.characterID = 0
		self.corporationName = ""
		self.allianceName = None
		self.allianceID = None
		self.API_id = 0
		self.API_vcode = 0
		self.default_character = 0
		
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
			
	def dump(self):
		return self.skills		