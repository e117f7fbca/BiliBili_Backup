#!/usr/bin/env python3
import re
import time
import sys
import os
import json
import glob
import hashlib
import zipfile

count=0

alluser=sorted(os.listdir(dyndir))
dyndir='/mnt/P4501/Raw/BB/Realtime/uid477306079/dynamic/'
dynstat=sorted(os.listdir(dyndir))

for eachdynpath in dynstat:
    if os.path.exists(os.path.join(dyndir,eachdynpath,"like.json")):
        with open(os.path.join(dyndir,eachdynpath,"like.json"), 'r',encoding='utf-8') as f:
            like_json=json.loads(f.read())
            count=count+len(like_json)

print(count)