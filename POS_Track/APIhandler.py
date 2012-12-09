#!/Python27/python.exe

from xml.dom import minidom

#####API PATHS#####
basepath="https://api.eveonline.com"
keyinfo="/account/APIKeyInfo.xml.aspx"
corpAsset="/corp/AssetList.xml.aspx"
corpStarbase="/corp/StarbaseDetail.xml.aspx"
corpPOSdetail="/corp/StarbaseList.xml.aspx"
validMask=2&131072&524288

def APIload (APIdict, CHARdic):
	for key in APIdict:
		keyinfoURL = basepath+keyinfo+"?keyID="+key+"vCode="+APIdict[key]
		API_keyinfo = minidom.parse(urllib.urlopen(keyinfoURL))
		
		if APIvalid (API_keyinfo, "corp", validMask) and APIcorp(API_keyinfo

