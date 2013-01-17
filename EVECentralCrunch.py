#!/Python27/python.exe

import csv


data   = csv.reader(open("test.dump"))

fields = data.next()

	#Loads dump file into dictionary of dictionary
	#AllTheThings[<orderid>]=[orderid:##,regionid:##,systemid:##..
allTheThings = {}
for row in data:
	items = zip(fields, row)
	item = {}

	for (name,value) in items:
		item[name] = value.strip()
	allTheThings[item["orderid"]]=item

##Filter Set##
SystemFilter = "30000142"

cleanList = {}
