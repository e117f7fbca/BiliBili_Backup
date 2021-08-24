# BiliBili_Backup

一个备份B站UP主内容的脚本，低技术力，仅供参考

#备份内容:
###UP主空间  
    头像（face.jpg）  
    banner（top_photo.jpg）  
    关注数（stat.json）  
    个人介绍（info.json）  
###动态  
    动态原数据（dynamic.json）（内容、浏览、点赞、转发、原动态）  
    动态评论（comment.json）（评论区内容）  
    动态点赞列表（like.json）(点赞用户ID，点赞时间)  
    图片（/picture/1.jpg）  
    转发动态原动态（/origin/dynamic）  
    小视频动态(svideo.mp4)  
###视频  
    视频分P（cidXXXXXXX）（调用annie下载）  
    视频信息（info.json）  
    视频统计（stat.json）  
    视频tag（tag.json）  
    分P信息（view.json）  
    视频评论（comment.json）  
    视频封面（cover.jpg）  
###音频  
    音频本体（audio.m4a）  
    音频信息（info.json）  
    音频tag（tag.json）  
    音频封面（cover.jpg）  
    音频评论（comment.json）  

json更新后，原json会压缩至同名文件夹内"日期.zip"存档，文件名为UTC时间戳  
