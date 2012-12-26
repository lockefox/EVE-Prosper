#!/Python27/python.exe

from xml.dom import minidom
import pos_crunch

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
	for dom_row in domcall.getElementsByTagName('row'):
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
debug_poslist = POS_list(API_debug,1,1)
#print debugobj.type
print debug_poslist