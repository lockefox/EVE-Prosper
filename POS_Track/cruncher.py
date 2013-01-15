import time
import tempfile
import cPickle
import zlib
import os
from os.path import join, exists
from httplib import HTTPException

import json
import eveapi
import pos_crunch

keysFile = "keys.json"

keys_json = open(keysFile)
keys = json.load(keys_json)

for key_list in keys{"corpAPIs"}
	