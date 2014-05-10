import MySQLdb
import ConfigParser

import blueprints
import characters
import systems
import factories
#import teams

###TODO: single config parser on import?
conf = ConfigParser.ConfigParser()
conf.read(["init_tmp.ini","init.ini"])

class Job:
	#Job takes:
	#	- Blueprint
	#	- Character
	#	- System
	#	- Factory
	#	- Team
	#
	#	- Runs (or time)
	#	- Cost of output
	#
	#Job returns:
	#	- Bill of Materials
	#	- Estimated cost of job
	def __init__(self):
		
		
		pass
		