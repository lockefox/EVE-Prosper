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
data   = csv.reader(open("Jita_trit_sell.dump.csv"))

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
SystemFilter = "30000142"

cleanlist = {}
#cleanlist {itemID:{buy:{max:,min:,avg:,...},sell:{max:,min:,avg:...}}}

if SystemFilter is "":
	#GlobalCase.  Process all data as global'
	print "global case"
else:
	for orderid,data in allTheThings.iteritems():
		buy_or_sell = "sell"
		if int(data["bid"]) == 1:
			buy_or_sell = "buy"
		
		if data["typeid"] in cleanlist:
			if data["systemid"] in cleanlist[data["typeid"]]:
				if buy_or_sell in cleanlist[data["typeid"]][data["systemid"]]:
						#existing entry case
						#general data values
					if float(data["price"]) > cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"]:
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"]=float(data["price"])
					if float(data["price"]) < cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"]:
						cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"]=float(data["price"])
						
					temp = cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] + int(data["volenter"])
					delta = float(data["price"]) - cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"]
					R = delta * (int(data["volenter"])/temp)
					
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] += R
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] += (cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] * delta * R)
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] += long(data["volenter"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"]/cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"]
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = math.sqrt(cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"])
					
					print "+%s\t=%d" %(data["volenter"],cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"])
				else:
					#typeid AND system exist, but not buy/sell key
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
					
						#initialize general data values#
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
					
						#initialize running-average values#
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
					cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
			else:
					#typeid exists, but not for this system
				cleanlist[data["typeid"]][data["systemid"]]={}
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
				
					#initialize general data values#
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
				
					#initialize running-average values#
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
				cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
		else:
				#initialize totally new key
			cleanlist[data["typeid"]] = {}
			cleanlist[data["typeid"]][data["systemid"]]={}
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]={}
			
				#initialize general data values#
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["max"] = float(data["price"])
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["min"] = float(data["price"])
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["avg"] = float(data["price"])
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["vol"] = long(data["volenter"])
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["region"] = int(data["regionid"])
			
				#initialize running-average values#
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["M2"] = 0
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["var"] = 0
			cleanlist[data["typeid"]][data["systemid"]][buy_or_sell]["stdev"] = 0
			
			print data["volenter"]
print cleanlist	["34"][SystemFilter]

