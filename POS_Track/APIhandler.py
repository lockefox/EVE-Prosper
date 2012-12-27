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


def APIvalidator (domcall, which, mask):
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
	
	type = domcall.getElementsByTagName('key')[0].getAttribute("type")
	CAKmask = int(domcall.getElementsByTagName('key')[0].getAttribute("accessMask"))
	expiry = domcall.getElementsByTagName('key')[0].getAttribute("expires")
	
	if expiry != "":
		expire_time=time.strptime(expiry,"%Y-%m-%d %H:%M:%S")
		UTC_now= time.gmtime()
		if expire_time < UTC_now:
			return "ERR: API Key Expired"
	
	if which == "Character":
		altwhich = "Account"
		
	else:
		altwhich = ""
	if type == which or type == altwhich:
		if type == "Corporation":
			if (CAKmask & CORP_mask[mask])== CORP_mask[mask]:
				return True
			else:
				return "ERR: Missmatch Mask.  Expected %d, API key is %d" % (CORP_mask[mask],CAKmask)
		else:	#character
			if (CAKmask & INDI_mask[mask])== INDI_mask[mask]:
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

def APIvalid (domcall, type, mask):
	#Returns TRUE or FALSE for the API call sent
	#API: /account/APIKeyInfo.xml.aspx
	#Type: Account, Character, Corporation
	#Mask: Desired CAK Access Mask
	#Expired: checks if given API is expired
	#IF all members match, TRUE
	#ELSE FALSE
	result = True
	info = APIcorp(domcall)
	
	if info.type != type:
		result = False
	if (info.mask & mask) != mask:
		result = False
	
	return result
	
class APIcorp(object):
	#handles some basic corp info from queries
	
	def __init__ (self, domcall):
		
		self.corpName	=domcall.getElementsByTagName('row')[0].getAttribute("corporationName")
		self.corpID		=int(domcall.getElementsByTagName('row')[0].getAttribute("corporationID"))
		self.charID 	=int(domcall.getElementsByTagName('row')[0].getAttribute("characterID"))
		self.charName	=domcall.getElementsByTagName('row')[0].getAttribute("characterName")
		self.mask		=int(domcall.getElementsByTagName('key')[0].getAttribute("accessMask"))
		self.type		=domcall.getElementsByTagName('key')[0].getAttribute("type")
		expire			=domcall.getElementsByTagName('key')[0].getAttribute("expires")
		
		#return for bool expired.  Empty = false, <current date = false, else true
		
def POS_list(domlist,key,vcode):
	#returns list of tower objects per corp ID
	index=0
	towerlist=[]
	for dom_row in domlist.getElementsByTagName('row'):
		towerinfo = Tower(dom_row,key,vcode)
		towerlist[index]=towerinfo
		index += 1
	
	return towerlist

def cachecheck(domcall):
	
	result = False
	cache_time = domcall.getElementsByTagName('cachedUntil')[0].nodeValue
	query_time = domcall.getElementsByTagName('currentTime')[0].nodeValue
	now_time = time.gmttime(time.time())

	
			
API_debug = minidom.parse("APIKeyInfo.xml")
debugobj = APIcorp(API_debug)
debug_valid = APIvalid(API_debug,"Corporation", validMask)
debug_valid = APIvalidator(API_debug, "Corporation", "POS")
print debug_valid
#debug_poslist = POS_list(API_debug,1,1)
#print debugobj.type
#print debug_poslist