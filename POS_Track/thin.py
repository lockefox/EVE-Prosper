#!/Python27/python.exe

from xml.dom.minidom import parse, parseString
import json
referenceFile = "itemlist.json"
reference_json = open(referenceFile)
reference = json.load(reference_json)

searchedID = 20063

itemid = reference["root"]["POSequipment"]["POSmods"][0]["itemID"]

#print itemid
found = False
for x in reference["root"]["POSequipment"]["POSmods"]:
	if x["itemID"] == searchedID:
		print searchedID,":",x["name"]
		found = True
		
	#print x
if found == False:
	print "did not find ID"
	