#!/Python27/python.exe

from xml.dom import minidom
import pos_crunch
import datetime
import time

#####API PATHS#####
basepath="https://api.eveonline.com"
keyinfo="/account/APIKeyInfo.xml.aspx"
corpAsset="/corp/AssetList.xml.aspx"
corpStarbase="/corp/StarbaseDetail.xml.aspx"
corpPOSdetail="/corp/StarbaseList.xml.aspx"
validMask=2|131072|524288	#Valid API's required for all calls requested

##### DOM Objects #####

##### Queries Handler #####
##	General data structures for handling multiple API calls to multiple entities


def APIvalidator (domcall, which, mask, limit_mask):
	#	ARGS=(which, mask, limit_mask)
	#Accepts domcall from APIinfo
	#Returns TRUE if both the API mask is valid AND not past expiry date
	
	#API Masks: http://wiki.eve-id.net/APIv2_Page_Index
	INDI_mask={		#All valid individual API masks
		"Account Balance":	1,
		"Assets":			2,
		"Calendar":			4|1048576,
		"Char Sheet":		8,
		"Contacts":			16|32,
		"Contracts":		67108864,
		"FW":				64,		
		"Kills":			256,
		"Locations":		134217728,
		"Mail Bodies":		512,
		"Mail Lists":		1024,
		"Mail Heads":		2048,
		"Orders":			4096,
		"Medals":			8192,
		"Notifications":	16384|32768,
		"Skill Queue":		131072|262144,
		"Standings":		524288,
		"Wallet Journal":	2097152,
		"Transactions":		4194304,
		#Custom masks -- OR together required masks
		"Trade":			2097152|4194304|4096|67108864,
		"Mail":				512|1024|2048|16384|32768,
		"Industry":			128|65536,
		"Skills":			8|131072|262144
	}
	CORP_mask={		#All valid Corp API masks
		"Wallets":			1,
		"Assets":			2,
		"Contacts":			16,
		"Containers":		32,
		"Contracts":		8388608,
		"Info":				8,
		"FW":				64,
		"Industry":			128,
		"Kills":			256,
		"Locations":		16777216,
		"Orders":			4096,
		"Medals":			8192,
		"Member Medals":	4,
		"Member Titles":	512,
		"Member Log":		1024,
		"Member Track":		2048,
		"Outpost List":		16384,
		"Outpost Service":	32768,
		"Shareholders":		65536,
		"Standings":		262144,
		"POS Detail":		131072,
		"POS LIST":			524288,
		"Titles":			4194304,
		"Wallet Journal":	1048576,
		"Transactions":		2097152,
		#Custom masks -- OR together required masks
		"POS":				131072|524288|2,
		"Member":			4|512|1024|2048|4194304,
		"Trade":			1|4096|1048576|2097152
	}
		#query APIinfo#
	type = domcall.getElementsByTagName('key')[0].getAttribute("type")
	CAKmask = int(domcall.getElementsByTagName('key')[0].getAttribute("accessMask"))
	expiry = domcall.getElementsByTagName('key')[0].getAttribute("expires")
	
	if expiry != "":
		expire_time=time.strptime(expiry,"%Y-%m-%d %H:%M:%S")	#http://www.tutorialspoint.com/python/time_strptime.htm
		UTC_now= time.gmtime()
		if expire_time < UTC_now:
			return "ERR: API Key Expired"
	
	if which == "Character":
		altwhich = "Account"
		
	else:
		altwhich = ""
	if type == which or type == altwhich:
		if type == "Corporation":
			if (CAKmask & CORP_mask[mask])== CORP_mask[mask] and (CAKmask & limit_mask)== limit_mask:
				return True

			else:
				return "ERR: Missmatch Mask.  Expected %d, API key is %d" % (CORP_mask[mask],CAKmask)	#Touple for numbers
		else:	#character
			if (CAKmask & INDI_mask[mask])== INDI_mask[mask] and (CAKmask & limit_mask)== limit_mask:
				return True

			else:
				return "ERR: Missmatch Mask.  Expected %d, API key is %d" % (INDI_mask[mask],CAKmask)
	
	else:
		return "ERR: Missmatch type.  Expected %s, API key is %s" % which,type
	
	
def APIload (APIdict, CHARdic):
	for key in APIdict:
		keyinfoURL = "%s%s?keyID=%s&vCode=%s" % basepath,keyinfo,key,APIdict[key]
		API_keyinfo = minidom.parse(urllib.urlopen(keyinfoURL))
		
		if APIvalid (API_keyinfo, "Corporation", validMask) and not (APIcorp(API_keyinfo).corpName in APIlist):
			stuff


	
class APIcorp(object):
	#Collect all relevant domcall objects 
	limit_mask=0
	def __init__ (self, *args):
			#	ARGS: key, vcode, limit_mask (optional)
		arg_list = list(args)
		if len(arg_list) > 3:
			limit_mask=arg_list[2]
		key = arg_list[0]
		vcode=arg_list[1]
		APIinfo_dom = minidom.parse(urllib.urlopen("%s/account/APIKeyInfo.xml.aspx?keyID=%s&vCode=%s" % basepath,key,vcode))
		self.charID = int(APIinfo_dom.getElementsByTagName('row')[0].getAttribute("characterID"))
		self.character=APIinfo_dom.getElementsByTagName('row')[0].getAttribute("characterName")
		self.corp = APIinfo_dom.getElementsByTagName('row')[0].getAttribute("corporationName")
		self.corpID=int(APIinfo_dom.getElementsByTagName('row')[0].getAttribute("corporationID"))
		
	#APIcorp holds dom objects for all corp APIs.  Queried at object call.
	#limit_mask can be added to only query certain APIs (and leave the rest untouched.  Default = 0
	#each API type (wallet, assets, etc) will either have the dom object or error message
		if APIvalidator (APIinfo_dom, "Corporation", "Wallet", limit_mask):
			self.wallet = minidom.parse(urllib.urlopen("%s/corp/AccountBalance.xml.aspx?keyID=%s&vCode=%s&characterID=%d" % basepath,key,vcode,charID))
		else:
			self.wallet = APIvalidator (APIinfo_dom, "Corporation", "Wallet", limit_mask)
		
		if APIvalidator (APIinfo_dom, "Corporation", "Assets", limit_mask):
			self.assets = minidom.parse(urllib.urlopen("%s/corp/AssetList.xml.aspx?keyID=%s&vCode=%s" % basepath,key,vcode))
		else:
			self.assets = APIvalidator (APIinfo_dom, "Corporation", "Assets", limit_mask)
		
		if APIvalidator (APIinfo_dom, "Corporation", "Contacts", limit_mask):
			self.contacts = minidom.parse(urllib.urlopen("%s/corp/ContactList.xml.aspx?keyID=%s&vCode=%s" % basepath,key,vcode))
		else:
			self.contacts = APIvalidator (APIinfo_dom, "Corporation", "Contacts", limit_mask)
			
		if APIvalidator (APIinfo_dom, "Corporation", "Containers", limit_mask):
			self.containers = minidom.parse(urllib.urlopen("%s/corp/ContainerLog.xml.aspx?keyID=%s&vCode=%s&characterID=%d" % basepath,key,vcode,charID)" % basepath,key,vcode))
		else:
			self.containers = APIvalidator (APIinfo_dom, "Corporation", "Containers", limit_mask)
		
		if APIvalidator (APIinfo_dom, "Corporation", "Contracts", limit_mask):
			self.contracts = minidom.parse(urllib.urlopen("%s/corp/Contracts.xml.aspx?keyID=%s&vCode=%s" % basepath,key,vcode))
		else:
			self.contracts = APIvalidator (APIinfo_dom, "Corporation", "Contracts", limit_mask)
			
			
API_debug = minidom.parse("APIKeyInfo.xml")
#debugobj = APIcorp(API_debug)
#debug_valid = APIvalid(API_debug,"Corporation", validMask)
debug_valid = APIvalidator(API_debug, "Corporation", "POS")
print debug_valid
#debug_poslist = POS_list(API_debug,1,1)
#print debugobj.type
#print debug_poslist