import json
import sys
import os
import time

UID=input("UID:")

uidlist=os.listdir(os.path.join(os.path.dirname(sys.path[0]),"Download"))
print(uidlist)
for eachuid in uidlist:
    dynamicpath=os.path.join(os.path.dirname(sys.path[0]),'Download',eachuid,'dynamic')
    if os.path.exists(dynamicpath):
        dynamiclist=os.listdir(dynamicpath)
        for eachdynamic in dynamiclist:
            likepath=os.path.join(dynamicpath,eachdynamic,'like.json')
            if os.path.exists(likepath):
                with open(likepath, 'r',encoding='utf-8') as f:
                    like_in_json=json.load(f)
                for eachlike in like_in_json:
                    uid=eachlike['uid']
                    name=eachlike['user_info']['uname']
                    timestrap=eachlike['time']

                    if str(uid)==str(UID):
                        print(str(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timestrap)))+" ["+str(name)+"] "+os.path.join(dynamicpath,eachdynamic))