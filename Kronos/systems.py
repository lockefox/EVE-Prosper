import MySQLdb
import ConfigParser

###TODO: single config parser on import?
conf = ConfigParser.ConfigParser()
conf.read(["init_tmp.ini","init.ini"])

class System:
	def __init__(self):
		self.systemID = 0
		self.systemName = ""
		self.regionID = 0
		self.regionName = ""
		self.security = 0.0
		
		self.stations = [] #stations[objStation,objStation]
		
		##TODO: modifier controllers.  Will see how much info/control is given

		self.jobHoursMod_
		self.FWmod = 0.0
		
class JobHours(System):
	def __init__(self):
		self.jobHoursMod_mfg = 0.0
		self.jobHoursMod_cpy = 0.0
		self.jobHoursMod_inv = 0.0
		self.jobHoursMod_me  = 0.0
		self.jobHoursMod_te  = 0.0
		self.jobHoursMod_re  = 0.0
		
		#TODO: link parent/child
	def __call__(self,jobKey):	#obj_JobHours(1=mfg) return job mod for mfg
		#TODO: automate off SDE?
		if isinstance(jobKey, (int, long)):
			#Move values into list and return off index for "cleaner" code?
			jobKey = int(jobKey)	#typecast to avoid issue later?
			if jobKey == 1:		#manufacturing
				return self.jobHoursMod_mfg
			elif jobKey == 2:	#"Technology Research"
				return None
			elif jobKey == 3:	#Time Research
				return self.jobHoursMod_te
			elif jobKey == 4:	#Material Research
				return self.jobHoursMod_me
			elif jobKey == 5:	#Copying
				return self.jobHoursMod_cpy
			elif jobKey == 7:	#Reverse Engineering
				return self.jobHoursMod_re
			elif jobKey == 8:	#Invention
				return self.jobHoursMod_inv
			else:
				raise Exception #TODO: more useful exception
		elif is isinstance(jobKey, basestring):
			if jobKey == "Manufacturing":
				return self.jobHoursMod_mfg
			elif jobKey == "Researching Technology":	
				return None
			elif jobKey == "Researching Time Productivity":	
				return self.jobHoursMod_te
			elif jobKey == "Researching Material Productivity":
				return self.jobHoursMod_me
			elif jobKey == "Copying":
				return self.jobHoursMod_cpy
			elif jobKey == "Reverse Engineering":
				return self.jobHoursMod_re
			elif jobKey == "Invention":
				return self.jobHoursMod_inv
			else:
				raise Exception #TODO: more useful exception	
		else:
			raise Exception	#todo: more useful exceptions
		
	def fetchModifiers(self):
		pass	#TODO: need to figure out API/local config
		
class Station(System):	#Stations are children to systems
		#This ~should~ allow dynamic control of job cost modifiers?
		#Reliant on modifier API/SDE
	def __init__(self):
		self.tax = 0.0
		self.facilityReduction = 0.0
		pass