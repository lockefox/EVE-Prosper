#!/Python27/python.exe

import csv, sys, math
def lineproc (line):
	type = ""
	if int(line["bid"]) == 1:
		type = "buy"
	else:
		type = "sell"
		
	item = str(line["typeid"])
	
	if item in cleanList and type in cleanList[item]:	#if ITEM entry AND buy or sell sub-dict exist
		#existing entry case
		if float(line["price"]) > cleanList[item][type]["max"]:
			cleanList[item][type]["max"] = float(line["price"])
		if float(line["price"]) < cleanList[item][type]["min"]:
			cleanList[item][type]["min"] = float(line["price"])
		
		
		temp = cleanList[item][type]["vol"] + int(line["volremain"])
		delta = float(line["price"]) - cleanList[item][type]["mean"]
		R = delta * (int(line["volremain"])/temp)
		cleanList[item][type]["mean"] = cleanList[item][type]["mean"] + R
		cleanList[item][type]["M2"] = cleanList[item][type]["M2"] + (cleanList[item][type]["vol"] * delta * R)
		cleanList[item][type]["vol"] = temp
		cleanList[item][type]["variance"] = cleanList[item][type]["M2"]/cleanList[item][type]["vol"]
		
			#total data metrics built by WEIGHTED INCREMENTAL ALGORITHM
		#cleanList[item][type]["vol"] += int(line["volremain"])
		#delta = float(line["price"]) - cleanList[item][type]["mean"]
		#cleanList[item][type]["mean"] = cleanList[item][type]["mean"] + delta/cleanList[item][type]["vol"]
		#cleanList[item][type]["M2"] = cleanList[item][type]["M2"] + delta * (float(line["price"])-cleanList[item][type]["mean"])
		#cleanList[item][type]["variance"] = cleanList[item][type]["M2"]/(cleanList[item][type]["vol"]-1)
		#cleanList[item][type]["stdev"] = math.sqrt(cleanList[item][type]["variance"])
		
	else:
		#new entry case
			#init dict of dict higher keys
		cleanList[item]={}
		cleanList[item][type]={}
		
		cleanList[item][type]["max"] = float(line["price"])
		cleanList[item][type]["min"] = float(line["price"])
		
			#initial data metrics from ONLINE ALGORITHM
		cleanList[item][type]["vol"] = int(line["volremain"])	#n
		cleanList[item][type]["mean"] = float(line["price"])		#mean
		cleanList[item][type]["M2"] = 0							#stdev
		cleanList[item][type]["variance"] = 0					#variance
		cleanList[item][type]["stdev"] = 0						#stdev

		
		
		

dumpfile = "/central_dumps"		#Download all the raw files intended for crunch
data   = csv.reader(open("2012-01-01.dump"))

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

print "processed datafile"
##Filter Set##
SystemFilter = 30000142

cleanList = {}
#cleanlist {itemID:{buy:{max:,min:,avg:,...},sell:{max:,min:,avg:...}}}

if SystemFilter is "":
	#GlobalCase.  Process all data as global'
	print "global case"
else:
	for orderid,data in allTheThings.iteritems():
		#print data["systemid"]
		if int(data["systemid"]) == SystemFilter:
			lineproc(data)
		

print cleanList	["34"]

