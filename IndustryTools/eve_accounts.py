#!/Python27/python.exe

import sys, gzip, StringIO, csv, sys, math, os, getopt, subprocess, math, datetime, time, json, socket
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import MySQLdb
import ConfigParser

import eve_characters
from eveapi import eveapi
#import eveapi


conf = ConfigParser.ConfigParser()
conf.read(["init.ini","tmp_init.ini"])

api_file = conf.get("EVE_ACCOUNTS","api_list")
backup_path = conf.get("EVE_ACCOUNTS","char_backup_path")
api_basepath = conf.get("GLOBALS","api_basepath")
user_agent = conf.get("GLOBALS","user_agent")

api = eveapi.EVEAPIConnection()

class KeyInfo:
	def __init__ (self,keyID,vCode):
		self.keyID = keyID
		self.vCode = vCode
		self.accessMask = 0
		self.type = ""
		self.expires = ""
		self.auth=api.auth(keyID = self.keyID, vCode = self.vCode)
		self.fetch_keyInfo()
	def fetch_keyInfo(self):
		apiauth = self.auth
		try:
			apikeyinfo = apiauth.account.APIKeyInfo()
		except eveapi.Error, e:	#regular eveapi errors
			raise e
		except Exception, e:	#bigger issues (socket errs, fires, earthquakes, floods, dogs and cats living together)
			raise e
		
		self.accessMask = apikeyinfo.key.accessMask
		self.expires = apikeyinfo.key.expires
		self.type = apikeyinfo.key.type
		
def fetch_characters(key_obj):
		#fetches /account/Characters.xml.aspx
		#returns list of char names/id's associated with account
		#for auto-completing api.json data
	list_of_characters = []
	try:
		characterAPI = key_obj.auth.account.Characters()
	except eveapi.Error, e:	#regular eveapi errors
		raise e
	except Exception, e:	#bigger issues (socket errs, fires, earthquakes, floods, dogs and cats living together)
		raise e
		
	for character in characterAPI.characters:
		tmp_char_dict = {}
		tmp_char_dict["name"] = character.name
		tmp_char_dict["characterID"] = character.characterID
		tmp_char_dict["corporationID"] = character.corporationID
		tmp_char_dict["corporationName"] = character.corporationName
		list_of_characters.append(tmp_char_dict)
	return list_of_characters
	
def fetch_characterSheet(key_obj,characterID,enableDump=1):
		#fetches character Sheet from /char/CharacterSheet.xml.aspx
		#returns a dict of characters: D_O_C[characterID]=Character()
	CAK_mask = 8
	if (key_obj.accessMask & CAK_mask) != CAK_mask:
		raise KeyError("invalid accessMask.  Requires: %s" % CAK_mask)
	if key_obj.type != "Account":
		raise KeyError("invalid keyType.  Requires 'Account'")
	
	Parsed_Character = eve_characters.Character()
	try:
		characterSheet = key_obj.auth.char.CharacterSheet(characterID=characterID)
	except Exception as e:
		raise e
	
	#print characterSheet.name
	Parsed_Character.load_eveapi(characterSheet)
	print "\t%s" % Parsed_Character
	if enableDump:
		dump_filename = "%s_characterSheet.XML" % Parsed_Character.name
		dump_apiArgs = "characterID=%s" % characterID
		API_localDumper(key_obj,"/char/CharacterSheet.xml.aspx",dump_filename,dump_apiArgs)
	
	return Parsed_Character
	
def fetch_allCharacters(apiFile=api_file):
	print "Fetching Characters"
	character_dict = {}		#character_dict[characterID]=Character()
	
	api_todo = json.load(open(apiFile))
	characterIndx = 0
	for api_obj in api_todo:
		#test api/connection
		try:
			api = KeyInfo(api_obj["keyID"],api_obj["vCode"])
		except eveapi.Error, e:	#regular eveapi errors
			print "Invalid key combo: %s\t%s" % (api_obj["keyID"],api_obj["vCode"])
			continue
		except Exception, e:
			print "Unable to fetch API: %s" % e
			print "--Continuing offline--"
			character_dict = fetch_allCharacters_offline(character_dict)
			break
		#update local API db
		api_todo[characterIndx]["accessMask"] = api.accessMask
		api_todo[characterIndx]["expiration"] = api.expires
		
		character_list = fetch_characters(api)
		api_todo[characterIndx]["characters"] = character_list
		tmp_character_dict = {}
		for character_obj in character_list:
			tmp_character_dict[character_obj["characterID"]] = fetch_characterSheet(api,character_obj["characterID"])
			
	return character_dict
def fetch_allCharacters_offline(all_character_dict, backupDump = backup_path):
	test=1
	files_to_parse = os.listdir(backupDump)
	return all_character_dict
def API_localDumper(key_obj,api_path,fileName,optional_args=""):
	api_query = "%s/%s?keyID=%s&vCode=%s" % (api_basepath,api_path,key_obj.keyID,key_obj.vCode)
	if optional_args != "":
		api_query = "%s&%s" % (api_query,optional_args)
	
	request = urllib2.Request(api_query)
	request.add_header('Accept-Encoding','gzip')
	request.add_header('User-Agent',user_agent)
	
	try:
		opener = urllib2.build_opener()
		header_hold = urllib2.urlopen(request).headers
		raw_zip = opener.open(request)
		dump_zip_stream = raw_zip.read()
	except urllib2.HTTPError as e:
		print e
		print "did not dump: %s" % api_query
		return
	except urllib2.URLError as er:
		print e
		print "did not dump: %s" % api_query
		return
	except socket.error as err:
		print e
		print "did not dump: %s" % api_query
		return
	
	dump_IOstream = StringIO.StringIO(dump_zip_stream)
	zipper = gzip.GzipFile(fileobj=dump_IOstream)
	xml_obj = minidom.parse(zipper)
	
	if not os.path.exists(backup_path):
		os.makedirs(backup_path)
	fileHandle = open(os.path.join(os.getcwdu(),backup_path,fileName),'w')
	fileHandle.write(xml_obj.toxml())	#dump XML raw to specified file
def main():
	test=0
	fetch_allCharacters()
if __name__ == "__main__":
	main()