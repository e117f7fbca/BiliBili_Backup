
#!/usr/bin/env python3
import os
import time
import sys
import subprocess
from subprocess import DEVNULL
import re
import random

##############################################################################################################################
def set_block(blockfile_path):
    with open(blockfile_path, 'w') as f:
        f.write(str(int(time.time())))
##############################################################################################################################
def check_block(blockfile_path,blocksecond):
    if os.path.exists(blockfile_path) == False:
        return False
    else:
        with open(blockfile_path, 'r') as f:
            lastlock=int(f.read())
            if time.time()-lastlock>blocksecond:
                #Block超时
                subprocess.call("rm "+blockfile_path,shell=True,stderr=DEVNULL)
                return False
            else:
                #仍在Block
                return True
##############################################################################################################################
def ppp_redial(block_folder):
    print("ppp watch dog start")
    while True:
        if os.path.exists(os.path.join(block_folder,'Direct')):

            print(str(time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime()))+" Start redial")            

            ip_direct_now=ppp_getip()+"_Direct"
            set_block(os.path.join(block_folder,ip_direct_now))

            newmac=ppp_genmac()
            #print("New MAC Address: "+newmac)
            subprocess.call("ip link set eth1 address "+newmac,shell=True,stderr=DEVNULL)
            time.sleep(0.1)

            #print("Interface Up")
            subprocess.call("ifup PPPD",shell=True,stderr=DEVNULL)

            while True:
                if ppp_getip() != None:
                    break
                else:
                    time.sleep(0.01)
                    
            ip_direct_new=ppp_getip()+"_Direct"

            if check_block(os.path.join(block_folder,ip_direct_new),301):
                print(str(time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime()))+" Not good")  
                time.sleep(3)
            else:
                print(str(time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime()))+" Good")  
                try:
                    os.remove(os.path.join(block_folder,'Direct'))
                except:
                    pass
                time.sleep(1)
        time.sleep(0.01)
##############################################################################################################################
def ppp_getip():
    while True:
        p=subprocess.run('ip addr show pppoe-PPPD', shell=True,capture_output=True)
        out = p.stdout.decode(encoding="utf-8")
        rematch=re.search(r'inet [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',out)
        try:
            if rematch !=None:
                ipaddr=rematch[0].replace("inet ","")
                return ipaddr
        except:
            time.sleep(0.01)
##############################################################################################################################
def ppp_genmac():
    possible='abcdef123456789'
    mac="a0:36:9f:"+random.choice(possible)+random.choice(possible)+":"+random.choice(possible)+random.choice(possible)+":"+random.choice(possible)+random.choice(possible)
    return mac
##############################################################################################################################


if  __name__ == "__main__":
    block_folder="/tmp/BB_Block"
    if not os.path.exists(block_folder):
        os.mkdir(block_folder)
    ppp_redial(block_folder)