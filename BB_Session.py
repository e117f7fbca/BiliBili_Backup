#!/usr/bin/env python3

import re
import time
import sys
import os
import json
import shutil
import hashlib
import glob

import requests

import subprocess
from subprocess import DEVNULL

from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED#线程池支持
import multiprocessing

import zipfile
import random

##############################################################################################################################
# annie参数
anniepath=os.path.join(sys.path[0],'annie')
anniecookie=os.path.join(sys.path[0],'cookie.txt')
annieprocess=8
annieproxy=""
##############################################################################################################################
def error_log(string):
    with open(os.path.join(os.path.join(sys.path[0],'log',"error.log")), 'a') as f:
        f.write(str(string)+'\n')
##############################################################################################################################
#抽取ua
def get_ua():
    version=random.choice(range(50,83))
    return "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:"+str(version)+".0) Gecko/20100101 Firefox/"+str(version)+".0"
##############################################################################################################################
#抽取代理
def get_proxy(proxyfile,proxy_q):
    with open(proxyfile, 'r',encoding='utf-8') as f:
        allproxy = f.readlines()    
        proxylist=[]

        for eachproxy in allproxy:
            try:
                #dic={}
                #dic['http']='https://'+eachproxy.split("##")[0].replace('\n','')
                #dic['https']='https://'+eachproxy.split("##")[0].replace('\n','')
                #dns_ua={"accept":"application/dns-json"}
                #dns_req=requests.get("https://cloudflare-dns.com/dns-query?name=api.bilibili.com&type=A",headers=dns_ua,timeout=1)
                #ip=json.loads(dns_req.content)['Answer'][2]['data']
                ip='128.1.62.201'
                proxylist.append([eachproxy.split("##")[0].replace('\n',''),float(eachproxy.split("##")[1].replace('\n','')),0.1,ip])
                print("proxy:"+eachproxy.split("##")[0].replace('\n','')+" destip:"+ip)
            except:
                pass

    
    while True:        
        for i in range(len(proxylist)):
            if float(time.time())-float(proxylist[i][2]) > float(proxylist[i][1]):
                dic={}
                dic['http']='http://'+proxylist[i][0]
                dic['https']='http://'+proxylist[i][0]
                proxylist[i][2]=float(time.time())
                lis=[dic,proxylist[i][3]]
                proxy_q.put(lis)
        pass
##############################################################################################################################
def run_annie(anniequeue):
    with ThreadPoolExecutor(max_workers=annieprocess) as annieexecutor:
        while True:
            annieexecutor.submit(subprocess.call,anniequeue.get(),shell=True)#,stdout=DEVNULL
            time.sleep(10)
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
#传入url和refer，传出响应对象
def try_get(session,url,refererurl):
    if url !="":
        header={}
        if "dynamic_like" in url:
            session.headers.update({'user-agent': "Mozilla/5.0 BiliDroid/6.12.0 (bbcallen@gmail.com) os/android model/LG-D858HK mobi_app/android build/6120400 channel/ss_baidusem_012 innerVer/6120400 osVer/6.0 network/2"})
        else:
            session.headers.update({'user-agent': get_ua()})
        
        if 'ugaxcode' in url:
            musicheader={'DNT':'1','Accept-Encoding':'identity;q:1, *;q=0','Accept':'*/*','Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'no-cors','Accept-Language':'zh-CN,zh;q=0.9'}
            session.headers.update(musicheader)

        session.headers.update(referer=refererurl)
        
        for tries in range(1,100):
        #while True:
            try:
                if conf_in_json['ppp_mode']:
                    if "hdslb" in url:
                        proxydic={"http":"192.168.1.1:8118","https":"192.168.1.1:8118"}
                        blockfile="Router"
                        r = requests.get(url,headers=header,proxies=proxydic,timeout=1)
                        if r.status_code ==200:
                            return r
                    else:
                        proxydic=None
                        blockfile="Direct"
                elif conf_in_json['proxy_mode']:
                    if "api" in url:
                        proxylis=proxy_q.get()
                        proxydic=proxylis[0]
                        proxydest=proxylis[1]
                        blockfile=str(proxydic['http'])[7:].replace(":","_")
                    else:
                        proxydic=None
                        blockfile="Direct"
                
                while check_block(os.path.join(block_folder,blockfile),3601):
                    time.sleep(0.01)

                try:
                    r = session.get(url,headers=header,proxies=proxydic,timeout=1)
                    if r.status_code ==200:
                        return r
                    elif r.status_code == 412:
                        set_block(os.path.join(block_folder,blockfile))
                        print("["+str(r.status_code)+"] "+url)
                        pass
                    elif r.status_code ==404 or r.status_code ==403 or r.status_code ==500:     
                        print("["+str(r.status_code)+"] "+url)
                        return None
                    else:
                        print("["+str(r.status_code)+"] "+url)
                        pass            
                except:
                    time.sleep(0.1)
                        
            except Exception as ee:
                print(ee)
                #time.sleep(100)
                pass
        return None
    return None

##############################################################################################################################
#传入json字符串，传出['data']
def json_data(input):
    text=json.loads(input)
    if 'status' in text:
        if text['status'] == True:
            return text['data']
    elif 'code' in text:
        if text['code'] == 0:
            return text['data']  
    else:
        return None

##############################################################################################################################
#传入mid，传出递增list格式的aid
def mid_avid_list(mid,download_mode):
    try:
        aidlistall = []
        for page in range(1, 20):
            tr = try_get(s,'https://api.bilibili.com/x/space/arc/search?mid=' + str(mid) + '&ps=100&tid=0&pn=' + str(page) + '&order=pubdate&jsonp=jsonp','https://space.bilibili.com/'+ str(mid))
            text = json_data(tr.content)
            try:
                aidlistall = aidlistall+text['list']['vlist']
            except:
                break
            if text['list']['vlist'] == None:
                break
        return list(reversed(aidlistall))
    except:
        return []
##############################################################################################################################
#传入mid，传出递增list格式的auid
def mid_auid_list(mid,download_mode):
    try:
        auidlistall = []
        for page in range(1, 20):
            #https://api.bilibili.com/audio/music-service/web/song/upper?uid=384064360&pn=1&ps=30&order=1&jsonp=jsonp
            tr = try_get(s,'https://api.bilibili.com/audio/music-service/web/song/upper?uid=' + str(mid) + '&ps=50&pn=' + str(page) + '&order=1&jsonp=jsonp','https://space.bilibili.com/'+ str(mid) + '/audio')
            
            if json_data(tr.content)['data'] == None:
                break
            else:
                auidlistall+=json_data(tr.content)['data']
        return list(reversed(auidlistall))
    except:
        return []

##############################################################################################################################
#传入mid，传出递增list格式的cvid
def mid_cvid_list(mid):
    try:
        r = try_get(s,'https://api.bilibili.com/x/space/article?mid=' +str(mid)+ '&pn=1&ps=12&sort=publish_time&jsonp=jsonp','https://space.bilibili.com/'+ str(mid)+'/article')
        cv = json_data(r.content)['articles']
        return cv
    except:
        return []

##############################################################################################################################
#传入oid，传出[{}{}{}{}{}{}{}{}]
def reply_comment(id,kind):
    try:
        #'PIC''TEXT''VIDEO''SVIDEOreply''AUDIO'

        if kind == 'VID':
            _type_=1
            refer_url='https://www.bilibili.com/video/av'+ str(id)
        if kind == 'SVID':
            _type_=5
            refer_url='https://t.bilibili.com/'+ str(id)
        elif kind == 'PIC':
            _type_=11
            refer_url='https://t.bilibili.com/'+ str(id)
        elif kind == 'ATC':
            _type_=12
            refer_url='https://t.bilibilreplycomi.com/'+ str(id)
        elif kind == 'AUD':
            _type_=14
            refer_url='https://www.bilibili.com/audio/au'+ str(id)
        elif kind == 'TXT':
            _type_=17
            refer_url='https://t.bilibili.com/'+ str(id)
        elif kind == 'REP':
            _type_=17
            refer_url='https://t.bilibili.com/'+ str(id)
        elif kind == 'SHA':
            _type_=17
            refer_url='https://t.bilibili.com/'+ str(id)
        else:
            _type_=17
            refer_url='https://t.bilibili.com/'+ str(id)

        reply = try_get(s,'https://api.bilibili.com/x/v2/reply?&jsonp=jsonp&pn=1&type='+str(_type_)+'&oid=' + str(id) + '&sort=0',refer_url)
        text = json_data(reply.content)
        if text == None or text['replies'] == None: 
            return []
        else:
            commentall = text['replies']

            countnum = text['page']['count']
            sizenum = len(text['replies'])
            request_num= (countnum // sizenum) + 3

            for pagenum in range(2,request_num):
                reply = try_get(s,'https://api.bilibili.com/x/v2/reply?&jsonp=jsonp&pn='+ str(pagenum) +'&type='+str(_type_)+'&oid=' + str(id) + '&sort=0',refer_url)
                text = json_data(reply.content)
                try:
                    commentall=commentall+text['replies']
                except:
                    pass
                
        return commentall
    except Exception as eee:
        print(eee)
        return None

##############################################################################################################################
#传入aid，传出list格式的cid
def aid_cid(aid):
    r = try_get(s,'https://api.bilibili.com/x/player/pagelist?aid=' +str(aid)+ '&jsonp=jsonp','https://www.bilibili.com/video/av'+ str(aid))
    text = json_data(r.content)
    return text

##############################################################################################################################
#传入mid，传出作者信息.json
def mid_info(mid):
    r = try_get(s,'https://api.bilibili.com/x/space/acc/info?mid=' +str(mid)+ '&jsonp=jsonp','https://space.bilibili.com/'+ str(mid))
    text = json_data(r.content)
    return text

##############################################################################################################################
def create_or_renew(folder,item,suffix,file):
    #folder
    #   item.suffix
    #   item
    #       time_item.suffix
    if not os.path.exists(folder):
        os.mkdir(folder)

    historyfolder= os.path.join(folder,item)
    oldpathfname= os.path.join(folder,item + '.' + suffix)

    #部分链接返回的是负载均衡域名，统一替换，以免MD5值不同
    if suffix == 'json' or suffix == 'html':
        file = file.decode('utf-8').replace('i1.hdslb.com','i0.hdslb.com').replace('i2.hdslb.com','i0.hdslb.com').encode('utf-8')

    try:
        #是否更新
        if os.path.exists(oldpathfname):
            try:
                #打开老文件
                with open(oldpathfname, 'rb') as oldf:
                    if len(file)!=os.path.getsize(oldpathfname) or hashlib.md5(file).hexdigest() != hashlib.md5(oldf.read()).hexdigest():         
                        
                        if not os.path.exists(historyfolder):
                            os.mkdir(historyfolder)

                        try:
                            oldtimestamp = int(os.stat(oldpathfname).st_mtime)
                            oldutctime=time.gmtime(oldtimestamp)
                            zipname=str(oldutctime.tm_year)+'-'+str(oldutctime.tm_mon).zfill(2)+'-'+str(oldutctime.tm_mday).zfill(2)+'_'+item+'.zip'
                            z = zipfile.ZipFile(os.path.join(folder,item,zipname), 'a')
                            z.write(oldpathfname,str(oldtimestamp) +'_'+ item + '.' + suffix,compress_type=zipfile.ZIP_LZMA)
                            z.close()
                        except Exception as e:
                            print(e)
                            pass

            except Exception as e:
                print(e)
                pass


            try:
                os.remove(oldpathfname)
                with open(oldpathfname, 'wb') as oldf:
                    oldf.write(file)
            except Exception as e:
                print(e)
                pass      
        
        else:
            with open(oldpathfname, 'wb') as oldf:
                oldf.write(file)
    except Exception as e:
        print(e)
        print("renew error")
        pass
    try:
        os.rmdir(historyfolder)#尝试删除空的历史文件夹
    except:
        pass

##############################################################################################################################
def downloadall(line,download_mode,threadnum):
    global s
    s = requests.Session()
    try:
        if '##' in line:
            try:
                mid=line.split("##")[0]
                info=mid_info(mid)
                print(info['name']+"——"+line.split("##")[1])
                authorpath = os.path.join(sys.path[0],'Download',"uid"+str(mid))
                try:
                    os.mkdir(authorpath)
                except:
                    pass
                
                #下载视频video
                try:
                    aidlist=mid_avid_list(mid,download_mode)
                    create_or_renew(os.path.join(authorpath,"video"),'vidlist','json',json.dumps(aidlist).encode())
                    for eachav in aidlist:
                        videodownload_sub(eachav,authorpath,download_mode)
                except Exception as e:
                    print("Video Error")

                if collect_meta:
                    #下载作者信息.json
                    authorinfo = try_get(s,'https://api.bilibili.com/x/space/acc/info?mid=' + str(mid) + '&jsonp=jsonp','https://space.bilibili.com/'+ str(mid))
                    create_or_renew(authorpath,'info','json',json.dumps(json_data(authorinfo.content)).encode())

                    #下载作者统计.json
                    authorstat = try_get(s,'https://api.bilibili.com/x/relation/stat?vmid=' + str(mid) + '&jsonp=jsonp','https://space.bilibili.com/'+ str(mid))
                    create_or_renew(authorpath,'stat','json',json.dumps(json_data(authorstat.content)).encode())  

                    #下载作者头像.jpg
                    authorface = try_get(s,info['face'],'https://space.bilibili.com/'+ str(mid))
                    create_or_renew(authorpath,'face','jpg',authorface.content)

                    #下载作者背景.jpg
                    authortop_photo = try_get(s,info['top_photo'],'https://space.bilibili.com/'+ str(mid))
                    create_or_renew(authorpath,'top_photo','jpg',authortop_photo.content)

                    #下载音频
                    try:
                        auidlist=mid_auid_list(str(mid),download_mode)
                        create_or_renew(os.path.join(authorpath,"audio"),'audlist','json',json.dumps(auidlist).encode())
                        for eachauid in auidlist:
                            audiodownload_sub(eachauid,authorpath,download_mode)
                    except Exception as e:
                        print("Audio Error")

                    #下载动态
                    try:
                        dynamicoffset=0
                        cardslist=[]
                        while True:
                            dy = try_get(s,'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid=' + str(mid) + '&offset_dynamic_id=' + str(dynamicoffset),'https://space.bilibili.com/'+ str(mid))
                            text = json.loads(dy.content)
                            try:
                                cardslist+=text['data']['cards']             
                                if dynamicoffset == 0:
                                    break
                                else:
                                    dynamicoffset=text['data']['next_offset']
                            except:
                                break
            
                        create_or_renew(os.path.join(authorpath,"dynamic"),'dynlist','json',json.dumps(cardslist).encode())
                        for eachcard in cardslist:
                            try:
                                dynamicdownload_sub(eachcard,authorpath,download_mode)
                            except:
                                pass
                    except Exception as e:
                        print("Dynamic Error")  

                    #下载文章
                    try:
                        cvidlist=mid_cvid_list(str(mid))
                        create_or_renew(os.path.join(authorpath,"article"),'atclist','json',json.dumps(cvidlist).encode())
                        for eachcvid in cvidlist:
                            articledownload_sub(eachcvid,authorpath,download_mode)
                    except Exception as e:
                        print("Article Error")

                print(line.replace("\n","")+" Finished")
            except Exception as e:
                print(e)
        else:
            print(line)
    except Exception as e:
        print(e)
        
##############################################################################################################################
def articledownload_sub(cv,authorpath,download_mode):
    if download_mode=="Lite" and (time.time()-cv["publish_time"]>7*24*60*60):
        print('└─cv'+str(cv['id'])+" skipped")
    elif collect_meta and False:#time.time()-cv["publish_time"]>6*30*24*60*60:
        print('└─cv'+str(cv['id'])+" half year skipped")
    else:
        # 输出cv号
        print('└─cv'+str(cv['id']))

        #作者目录下，cv[cvid]
        cvidpath = os.path.join(authorpath,'article','cv' +str(cv['id']))
        try:
            os.makedirs(cvidpath)
        except:
            pass

        #写入文章信息
        try:
            create_or_renew(cvidpath,'info','json',json.dumps(cv).encode())
        except Exception as e:
            print('文章信息错误')
            print(e)

        #下载banner
        try:
            banner=try_get(s,cv['banner_url'],'https://www.bilibili.com/read/cv'+ str(cv['id']))
            suffix = re.search(r'\.[A-za-z0-9]{1,10}$', cv['banner_url'])[0].replace('.','')
            create_or_renew(cvidpath,'banner',suffix,banner.content)
        except Exception as e:
            print('文章banner错误')
            print(e)


        #下载image
        try:
            for url in cv['image_urls']:
                try:
                    os.makedirs(os.path.join(cvidpath,'image'))
                except:
                    pass
                filename=re.search(r'[A-za-z0-9]{40}\.[A-za-z]{3,5}',url)[0]
                if os.path.exists(os.path.join(cvidpath,'image',filename)) == False:
                    r=try_get(s,url,'https://www.bilibili.com/read/cv'+ str(cv['id']))
                    open(os.path.join(cvidpath,'image',filename), 'wb').write(r.content) 
        except Exception as e:
            print('文章图片错误')
            print(e)      

        #下载origin_image
        try:
            for url in cv['origin_image_urls']:
                try:
                    os.makedirs(os.path.join(cvidpath,'origin_image'))
                except:
                    pass
                filename=re.search(r'[A-za-z0-9]{40}\.[A-za-z]{3,5}',url)[0]
                if os.path.exists(os.path.join(cvidpath,'origin_image',filename)) == False:
                    r=try_get(s,url,'https://www.bilibili.com/read/cv'+ str(cv['id']))
                    open(os.path.join(cvidpath,'origin_image',filename), 'wb').write(r.content) 
        except Exception as e:
            print('文章图片源文件错误')
            print(e)       
        
        #下载文章本体
        try:        
            r=try_get(s,'https://www.bilibili.com/read/cv'+ str(cv['id']),'https://www.bilibili.com/read/cv'+ str(cv['id']))
            create_or_renew(cvidpath,'article','html',r.content)
        except Exception as e:
            print('文章页面错误')
            print(e)
            pass

        #下载文章评论
        try:
            comment = json.dumps(reply_comment(cv['id'],'ATC'))
            create_or_renew(cvidpath,'comment','json',comment.encode())
        except Exception as e:
            print('文章评论错误')
            print(e)
            pass

##############################################################################################################################
def audiodownload_sub(au,authorpath,download_mode):
    if download_mode=="Lite" and (time.time()-au["curtime"]>7*24*60*60):
        print('└─au'+str(au['id'])+" skipped")
    elif collect_meta and False:#time.time()-au["curtime"]>6*30*24*60*60:
        print('└─au'+str(au['id'])+" half year skipped")
    else:
        # 输出au号
        print('└─au'+str(au['id'])) 
        #作者目录下，au[auid]
        auidpath = os.path.join(authorpath,'audio','au' +str(au['id']))
        try:
            os.makedirs(auidpath)
        except:
            pass

        #写入音频信息
        try:
            info=try_get(s,'https://www.bilibili.com/audio/music-service-c/web/song/info?sid='+str(au['id']),'https://www.bilibili.com/audio/au'+ str(au['id']))
            create_or_renew(auidpath,'info','json',json.dumps(json_data(info.content)).encode())
        except Exception as e:
            print('audio info')        
            print(e)

        #下载封面
        try:
            cover=try_get(s,au['cover'],'https://www.bilibili.com/audio/au'+ str(au['id']))
            suffix = re.search(r'\.[A-za-z0-9]{1,10}$', au['cover'])[0].replace('.','')
            create_or_renew(auidpath,'cover',suffix,cover.content)
        except Exception as e:
            print('audio cover')
            print(e)

        #下载音频
        try:
            linkinfo=try_get(s,'https://www.bilibili.com/audio/music-service-c/web/url?sid='+str(au['id'])+'&privilege=2&quality=2','https://www.bilibili.com/audio/au'+ str(au['id']))
            audiolink=json_data(linkinfo.content)['cdns'][0]
            audiofile=try_get(s,audiolink,'https://www.bilibili.com/audio/au'+ str(au['id']))
            suffix = re.search(r'\.[A-za-z0-9]{1,10}$', audiolink.split("?")[0])[0].replace('.','').replace('?','')
            create_or_renew(auidpath,'audio',suffix,audiofile.content)        
        except Exception as e:
            print('audio audio')
            print(e)

        #下载评论
        try:
            comment = json.dumps(reply_comment(au['id'],'AUD'))
            create_or_renew(auidpath,'comment','json',comment.encode())
        except Exception as e:
            print('audio comment')
            print(e)

        #下载tag
        try:
            tag = try_get(s,'https://www.bilibili.com/audio/music-service-c/web/tag/song?sid='+str(au['id']),'https://www.bilibili.com/audio/au'+ str(au['id']))
            create_or_renew(auidpath,'tag','json',json.dumps(json_data(tag.content)[0]).encode())
        except Exception as e:
            print('audio tag')
            print(e)

##############################################################################################################################
def videodownload_sub(av,authorpath,download_mode):
    if download_mode == 'Lite' and (time.time()-int(av['created'])>7*24*60*60):
        print('└─av'+str(av['aid'])+" skipped")
    elif collect_meta and False:#time.time()-int(av['created'])>6*30*24*60*60:
        print('└─av'+str(av['aid'])+" half year skipped")
    elif collect_video and ( ( ("生肉" in av["title"]) and ("字幕" not in av["title"]) ) or ("生肉合集" in av["title"]) ):
        print('└─av'+str(av['aid'])+" raw skipped")
    elif collect_video and ("FGO" in av["title"]):
        print('└─av'+str(av['aid'])+" FGO skipped")

    else:   
        #作者目录下，av[aid]
        aidpath = os.path.join(authorpath,'video','av' +str(av['aid']))
        
        try:
            os.makedirs(aidpath)
        except:
            pass

        if collect_meta:
            # 输出av号
            print('└─av'+str(av['aid']))

            # 下载aid的info.json{}
            try:
                create_or_renew(aidpath,'info','json',json.dumps(av).encode())
            except Exception as e:
                print('video info')
                print(e)
                pass
        
            # 下载aid的view.json{}
            try:
                view=try_get(s,"https://api.bilibili.com/x/web-interface/view?aid="+str(av['aid']),'https://www.bilibili.com/video/av'+str(av['aid']))
                viewjson=json_data(view.content)
                create_or_renew(aidpath,'view','json',json.dumps(viewjson).encode())
            except Exception as e:
                print('video view')
                print(e)
                pass
        
            # 下载aid的desc.json{}
            try:
                #https://api.bilibili.com/x/web-interface/archive/desc?aid=969706165&page=&jsonp=jsonp&callback=jsonCallback_bili_96573582498547080
                desc=try_get(s,"https://api.bilibili.com/x/web-interface/archive/desc?aid="+str(av['aid'])+"&page=&jsonp=jsonp",'https://www.bilibili.com/video/av'+str(av['aid']))
                descjson=json_data(desc.content)
                create_or_renew(aidpath,'desc','json',json.dumps(descjson).encode())
            except Exception as e:
                print('video desc')
                print(e)
                pass
        
            # 下载aid的stat.json{}
            try:
                #https://api.bilibili.com/x/web-interface/archive/stat?aid=969706165&jsonp=jsonp&callback=jsonCallback_bili_215496329767599584
                stat=try_get(s,"https://api.bilibili.com/x/web-interface/archive/stat?aid="+str(av['aid'])+"&page=&jsonp=jsonp",'https://www.bilibili.com/video/av'+str(av['aid']))
                statjson=json_data(stat.content)
                create_or_renew(aidpath,'stat','json',json.dumps(statjson).encode())
            except Exception as e:
                print('video stat')
                print(e)
                pass

            # 下载comment.json[{}{}{}]
            try:
                comment = json.dumps(reply_comment(av['aid'],'VID'))
                create_or_renew(aidpath,'comment','json',comment.encode())
            except Exception as e:
                print('video comment')
                print(e)

            # 下载tag.json{}
            try:    
                tag = try_get(s,'https://api.bilibili.com/x/tag/archive/tags?aid=' + str(av['aid']),'https://www.bilibili.com/video/av'+str(av['aid']))
                create_or_renew(aidpath,'tag','json',json.dumps(json_data(tag.content)[0]).encode())
            except Exception as e:
                print('video tag')
                print(e)

            # 下载视频封面
            try: 
                cover = try_get(s,'https://'+av['pic'][2:],'https://www.bilibili.com/video/av'+str(av['aid']))
                create_or_renew(aidpath,'cover','jpg',cover.content)
            except Exception as e:
                print('video cover')
                print(e)

        # 下载视频列表信息
        avpart=1
        cidlist = aid_cid(av['aid'])
        for cid in cidlist:
            cidpath = os.path.join(aidpath,'cid' +str(cid['cid']))
            
            #创建每个cid子文件夹
            try:
                os.mkdir(cidpath)
            except:
                pass

            if collect_meta:
                #下载view.json
                try:
                    view=try_get(s,"https://api.bilibili.com/x/web-interface/view?aid="+str(av['aid'])+'&cid='+str(cid['cid']),'https://www.bilibili.com/video/av'+str(av['aid']))
                    viewjson=json_data(view.content)             
                    create_or_renew(cidpath,'view','json',json.dumps(viewjson).encode())
                except Exception as e:
                    print('view.json Error')
                    print(e)
                    
                #下载弹幕
                try:
                    danmu = try_get(s,'https://api.bilibili.com/x/v1/dm/list.so?oid=' + str(cid['cid']),'https://www.bilibili.com/video/av'+str(av['aid']))
                    create_or_renew(cidpath,'danmu','xml',danmu.content)
                except Exception as e:
                    print('danmu.xml Error')
                    print(e)

                #下载字幕
                try:                
                    sublist = viewjson['subtitle']['list']
                    if sublist != []:
                        for eachsub in sublist:
                            eachsubbyte=try_get(s,eachsub['subtitle_url'],'https://www.bilibili.com/video/av'+str(av['aid'])).content
                            create_or_renew(cidpath,'subtitle_'+eachsub['lan'],'json',eachsubbyte)
                except Exception as e:
                    print(e)

            #生成annie脚本        
            if collect_video:
                if os.path.exists(os.path.join(cidpath,"video.flv")):
                    os.remove(os.path.join(cidpath,"video.mp4"))
                    os.rename(os.path.join(cidpath,"video.flv"),os.path.join(cidpath,"video.mp4"))
                anniecommand=annieproxy + anniepath+ ' -O video -o "' + cidpath +'"  -c "' + anniecookie +'" -r https://www.bilibili.com/video/av'+ str(av['aid']) +' av' +str(av['aid']) +'?p=' +str(avpart)
                if (os.path.exists(os.path.join(cidpath,"video.mp4"))) == False :
                    anniequeue.put(anniecommand)
                else:
                    pass
                    #print("Skip "+str(av['aid'])+" part " + str(avpart))

            avpart +=1

##############################################################################################################################
def dynamicdownload_sub(cardinfo,authorpath,download_mode):   
    #动态id号
    dynamicid=cardinfo['desc']['dynamic_id']

    # 1转发 2有图动态 4文字动态 8视频投稿 16小视频 32番剧更新 64专栏 256 音频
    dynamictype=cardinfo['desc']['type']

    if dynamictype == 1:
        dynamictype_text='REP'#回复
    elif dynamictype == 2:
        dynamictype_text='PIC'#图片动态
    elif dynamictype == 4:
        dynamictype_text='TXT'#文本动态
    elif dynamictype == 8:
        dynamictype_text='VID'#视频
    elif dynamictype == 16:
        dynamictype_text='SVID'#短视频
    elif dynamictype == 64:
        dynamictype_text='ATC'#专栏
    elif dynamictype == 256:
        dynamictype_text='AUD'#音频
    elif dynamictype == 512:
        dynamictype_text='ANI'#番剧
    elif dynamictype == 2048:
        dynamictype_text='SHA'#分享
    elif dynamictype == 4200:
        dynamictype_text='ACT'#活动
    elif dynamictype == 4300:
        dynamictype_text='COL'#收藏夹
    else:
        dynamictype_text='OTHER'


    if download_mode=="Lite" and (time.time()-cardinfo["desc"]['timestamp']>3*24*60*60):
        print('└─dyn'+str(dynamicid)+" skipped")
    elif collect_meta and False:#time.time()-cardinfo["desc"]['timestamp']>6*30*24*60*60:
        print('└─dyn'+str(dynamicid)+"half year skipped")
    else:
        print('└─dyn'+str(dynamicid))

        #根据动态id号创建每条动态独立文件夹
        dynamicpath=os.path.join(authorpath,'dynamic','dyn' +str(dynamicid))
        try:
            os.makedirs(dynamicpath)
        except:
            pass

        #下载动态.json
        create_or_renew(dynamicpath,'dynamic','json',json.dumps(cardinfo).encode())
        
        #下载有图动态内容
        if dynamictype_text =='PIC': 
    
            #有图动态图片路径
            dynamicpicpath= os.path.join(dynamicpath,'pictures')
            try:
                os.mkdir(dynamicpicpath)
            except:
                pass

            dynamicpiclist=eval(cardinfo['card'])['item']['pictures']
            picseq = 1
            for picinfo in dynamicpiclist:
                url = picinfo['img_src'].replace('\\','')
                suffix = re.search(r'\.[A-za-z0-9]{1,10}$', url)[0]
                if ~os.path.exists(os.path.join(dynamicpicpath,str(picseq)+suffix)):
                    pic = try_get(s,picinfo['img_src'].replace('\\',''),'https://t.bilibili.com/'+ str(dynamicid))
                    open(os.path.join(dynamicpicpath,str(picseq)+suffix), 'wb').write(pic.content)
                picseq +=1

        #下载小视频动态内容
        elif dynamictype_text == 'SVID':
            item = json.loads(cardinfo['card'])['item']
            scoversuffix = re.search(r'\.[A-za-z0-9]{3,10}?$', item['cover']["unclipped"])[0].replace('.','')
            scoverclippedsuffix = re.search(r'\.[A-za-z0-9]{3,10}?$', item['cover']["default"])[0].replace('.','')
            videosuffix = re.search(r'\.[A-za-z0-9]{3,10}?\?deadline', item['video_playurl'])[0].replace('?deadline','').replace('.','')
            
            if os.path.exists(os.path.join(dynamicpath,'svideo'+videosuffix)) == False:
                svideo=try_get(s,item['video_playurl'],'https://t.bilibili.com/'+ str(dynamicid))
                create_or_renew(dynamicpath,'svideo',videosuffix, svideo.content)
            
            if os.path.exists(os.path.join(dynamicpath,'cover'+scoversuffix)) == False:
                scover=try_get(s,item['cover']["unclipped"],'https://t.bilibili.com/'+ str(dynamicid))
                create_or_renew(dynamicpath,'cover',scoversuffix, scover.content)

            if os.path.exists(os.path.join(dynamicpath,'cover_clipped'+scoversuffix)) == False:    
                scoverclipped=try_get(s,item['cover']["default"],'https://t.bilibili.com/'+ str(dynamicid))
                create_or_renew(dynamicpath,'cover_clipped',scoverclippedsuffix, scoverclipped.content)

        elif dynamictype_text == 'REP':
            try:
                print(' └─dyn'+str(cardinfo['desc']['origin']['dynamic_id']))
                detail=try_get(s,"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id="+str(cardinfo['desc']['origin']['dynamic_id']),"https://t.bilibili.com/"+str(cardinfo['desc']['origin']['dynamic_id']))
                detail_data=json_data(detail.content)
                dynamicdownload_sub(detail_data['card'],os.path.join(dynamicpath,'origin'),download_mode)
            except Exception as ee:
                print(ee)
                
        if "item" in json.loads(cardinfo['card']) and "description" in json.loads(cardinfo['card'])['item'] and ("转发" in json.loads(cardinfo['card'])['item']['description'] or "评论" in json.loads(cardinfo['card'])['item']['description']) and "抽" in json.loads(cardinfo['card'])['item']['description']:
            print("Skip Useless dynamic")
        elif dynamictype_text != 'ANI' or dynamictype_text !='COL' or dynamictype_text != 'ACT':#番剧/收藏夹/活动/分享
            #获取动态评论.json
            try:
                rid = cardinfo['desc']['rid']
                commentlist = reply_comment(rid,dynamictype_text)
                if commentlist == []:
                    did = cardinfo['desc']['dynamic_id']#动态号
                    commentlist = reply_comment(did,dynamictype_text)
                    
                create_or_renew(dynamicpath,'comment','json', json.dumps(commentlist).encode())

            except Exception as e:
                print('Dynamic Comment Error')
                print(e)
                        
            #获取动态点赞.json
            try:
                like=try_get(s,"https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/spec_item_likes?access_key=2145306126003eb527a563688988b8b1&appkey=1d8b6e7d45233436&dynamic_id="+str(dynamicid)+"&pn=1&ps=50","https://t.bilibili.com/"+str(dynamicid))
                like_data=json_data(like.content)
                if 'item_likes' in like_data.keys():
                    likelist=like_data['item_likes']

                    request_num=( like_data['total_count'] // len(like_data['item_likes']) )+3

                    for each in range(2,request_num):
                        like=try_get(s,"https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/spec_item_likes?access_key=2145306126003eb527a563688988b8b1&appkey=1d8b6e7d45233436&dynamic_id="+str(dynamicid)+"&pn="+str(each)+"&ps=50","https://t.bilibili.com/"+str(dynamicid))
                        like_data=json_data(like.content)
                        try:
                            likelist=likelist+like_data['item_likes']
                        except:
                            pass

                    finallist=list(reversed(likelist))
                    create_or_renew(dynamicpath,'like','json', json.dumps(finallist).encode())
            except Exception as e:
                error_log("https://t.bilibili.com/"+str(dynamicid)+" Like Error + "+e)
                print('Dynamic Like Error')

##############################################################################################################################
if  __name__ == "__main__":
    
    config_json=os.path.join(sys.path[0],'config.json')

    if os.path.exists(config_json):
        with open(config_json, 'r',encoding='utf-8') as f:
            conf_in_json=json.load(f)
        threadnum=conf_in_json['threadnum']
        processnum=conf_in_json['processnum']

        collect_meta=conf_in_json['collect_meta']
        collect_video=conf_in_json['collect_video']

        if conf_in_json['block_folder']== "@Block":
            block_folder=os.path.join(sys.path[0],'Block')
        else:
            block_folder=conf_in_json['block_folder']
        subprocess.call("mkdir -p "+block_folder,shell=True,stderr=DEVNULL)

        if collect_video:
            anniequeue=multiprocessing.Queue(16)
            annierun = multiprocessing.Process(target=run_annie,args=(anniequeue,))
            annierun.start()

        if conf_in_json['proxy_mode']:
            proxyfile = (os.path.join(sys.path[0],'proxy.txt'))
            proxylist=[]
            with open(proxyfile, 'r',encoding='utf-8') as f:
                proxylist_raw=f.readlines()
                proxy_q = multiprocessing.Queue(len(proxylist_raw))
                proxy_watchdog = multiprocessing.Process(target=get_proxy,args=(proxyfile,proxy_q,))
                proxy_watchdog.start()
    else:
        print("No config.json find")
        time.sleep(10000)

    while True:
        
        allmid=sorted(os.listdir(os.path.join(sys.path[0],'Mid')))
        
        if conf_in_json['arrange'] == "parallel":
            starttime=time.time()   
            print("Pool start")
            litep=multiprocessing.Pool(processnum//2)
            fullp=multiprocessing.Pool(processnum//2)

            for eachmid in allmid:
                midfile = (os.path.join(sys.path[0],'Mid',eachmid))
                with open(midfile, 'r',encoding='utf-8') as f:
                    for each in f.readlines():
                        line=each.replace("\n","")
                        fullp.apply_async(downloadall,(line,"Full",threadnum,))
            print("Mid Full Fill")

            for seqnum in range(conf_in_json['ratio']):
                for eachmid in allmid:
                    midfile = (os.path.join(sys.path[0],'Mid',eachmid))
                    with open(midfile, 'r',encoding='utf-8') as f:
                        for each in reversed(f.readlines()):
                            line=each.replace("\n","")
                            litep.apply_async(downloadall,(line,"Lite",threadnum,))
            print("Mid Lite Fill")
            
            litep.close()
            fullp.close()
            litep.join()
            fullp.join()
            with open(os.path.join(sys.path[0],'log.txt'), 'a',encoding='utf-8') as f:
                f.write(str(time.strftime("[%Y-%m-%d %H:%M:%S]",time.localtime()))+" Process:"+str(processnum)+" Thread:"+str(threadnum)+" "+str(int(time.time()-starttime))+" seconds\n")
