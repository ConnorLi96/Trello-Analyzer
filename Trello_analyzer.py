#!/usr/bin/env python
# coding: utf-8

# In[86]:


import urllib.request
import re
import sys
import codecs
import json
from datetime import datetime
import os
import glob
import utils
import time
import getopt
import ssl


# In[42]:


import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei']#设置字体以便支持中文
plt.rcParams['savefig.dpi'] = 300 #图片像素
plt.rcParams['figure.dpi'] = 300 #分辨率
plt.rcParams['axes.unicode_minus']=False  #set for displaying `-


# In[14]:


# 设置参数

g_token = ""
g_app_key = ""
g_user_id = ""
g_board_id = ""
# g_board_id = ""
g_crontab_style = False

workload_pattern = u'[(（]\s*(\d+(?:\.\d+)?)\s*(pt|PT|pT|Pt)\s*[)）]' # 正则表达式
requirement_pattern = u'[\[【［]\s*(.*)\s*[】］\]]\s*' 


# In[15]:


def basic_replace(url): # 替换 url 等主要参数
    url = url.replace("_APP_KEY_", g_app_key)
    url = url.replace("_TOKEN_", g_token)
    return url


# In[16]:


def do_request(url): 
    context = ssl._create_unverified_context()
    request = urllib.request.Request(url) # urllib 网页抓取的库
    content = None
    flag = False

    for i in range(3):  # retry when network access failed 等于说这里是尝试了三遍
        try:
            response = urllib.request.urlopen(request, context= context) # 会验证一次 SSL 证书, 当目标使用的是自签名的证书时就会报 SSL 错误
            content = response.read().decode()
            flag = True # flag 应该是用来判断 try 是否执行成功
            break
        except urllib.request.HTTPError as e: # 给出报错信息
            print("http error: " + str(e))
        except Exception as e:
            print("error: " + str(e))

    if not flag:
        sys.exit(-1) # 没有 flag 说明报错了，然后退出程序

    if content is None:
        return []
    else:
        return json.loads(content)


# In[17]:


def get_card_name_by_pattern(card_name, pattern):
    return re.findall(pattern, card_name, re.S | re.U) # 搜索字符串，以列表类型返回全部能匹配的子串

def fetch_board_by_user():
    url = 'https://api.trello.com/1/members/_USERID_/boards?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_USERID_", g_user_id)
    body = do_request(url)
    board_info = {}

    for item in body:
        board_info[item['shortLink']] = item['name']

    return board_info # 拿到 board 的 name 和 shortlink 意味着可以放进 url 直接访问页面


# In[18]:


def insertStr(str_name): 
    
    if "[" in str_name: # 沙雕了。。。“[]”是意味着两个连在一起的
        str_list = list(str_name) # 字符数，可以利用这个在某个位置插入字
        str_pos = str_list.index('[') # 找到[ 的位置
        str_list.insert(str_pos, '\\') # 插入要插入的字符
        str_2 = "".join(str_list) # 将 list 转为 str
    
    else:
        str_2 = str_name
    
    return str_2


# In[19]:


def get_card_name_by_pattern(card_name, pattern):
    return re.findall(pattern, card_name, re.S | re.U)


# In[20]:


def fetch_list_id_by_board(list_pattern): # list_pattern 作为参数要输入 list name 
    url = 'https://api.trello.com/1/boards/_BOARDID_/lists?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_BOARDID_", g_board_id)
    body = do_request(url) # 返回那个 board 里所有的 list 信息
    list_info = []
    list_name = insertStr(list_pattern) # 识别 "[]" 
    
    for item in body:
        
        if re.search(list_name, item["name"], re.I) is not None: # re.search 在一个字符串中搜索匹配正则表达式的第一个位置，返回match对象
            list_info.append({'id': item['id'], 'name': item['name']}) 
            

    return list_info # 返回 list name 和 list_id


# In[21]:


def fetch_members_by_board(): # 拿到所有成员的名称和 id
    url = 'https://api.trello.com/1/boards/_BOARDID_/members?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_BOARDID_", g_board_id)
    body = do_request(url)
    all_members_info = {}

    for item in body:
        all_members_info[item['id']] = item['fullName']

    return all_members_info # 返回 id 和 member name


# In[22]:


def fetch_cards_by_list_id(list_id): #  可以通过上面的 fetch_list_id_by_board 可以获取 list_id
    url = 'https://api.trello.com/1/lists/_LISTID_/cards?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_LISTID_", list_id) 
    body = do_request(url)

    return body # 用 list_id 获取 cards 的所有信息




# ##  hours 统计 

# In[23]:


def get_cards_info(list_id, board_members):

    available_cards_info = []

    all_cards_info = fetch_cards_by_list_id(list_id)

    for item in all_cards_info:
        card_info = { # 设置很多空的 dict，然后依据后面的判断填入一些参数
            'id': item['id'],
            'card_name': item['name'],
            'member_id': None,
            'member_name': None,
            'label_id': None,
            'label_name': 'None',
            'plan_hours': 0,
            'actual_hours': 0 # 现在好像没有分 actual hours 和 plan 
        }

        idMembers = item['idMembers'] # 让 cards_info get 到 member 的信息
        if len(idMembers) > 0 and idMembers[0] is not None:
            member_id = idMembers[0]
            card_info['member_id'] = member_id
            card_info['member_name'] = board_members[member_id] # 这里不是报错是和 fetch_members_by_board 一起获得

        labels = item['labels']

        if len(labels) > 0 and labels[0] is not None: # 处理卡片的 labels
            label = labels[0]
            card_info['label_id'] = label['id']
            card_info['label_name'] = label['name']

        card_hours = get_card_name_by_pattern(item['name'], workload_pattern)
        
        if len(card_hours) == 2:
            card_info['actual_hours'] = float(card_hours[1][0]) * 2
            card_info['plan_hours'] = float(card_hours[0][0]) * 2
        else:
            card_info['actual_hours'] = float(card_hours[0][0]) * 2

            
        available_cards_info.append(card_info)
                       
    return available_cards_info
                       


# In[24]:


def generate_member_stat_from_cards_info(cards_info): # 这就写了个 dict 嘛，然后和 member 连接起来。cards_info 只需要是字典的格式就好了
    member_stat = {}

    # all_labels = list(set([value['label_name'] for value in cards_info.values()])) # cardinfo_turn_to_dict 拿到的 cards_info 没有label name
    for card_id in cards_info:
        member_stat[cards_info[card_id]['member_name']] = {
                                                            'plan_hours': 0,
                                                            'actual_hours': 0,
                                                            'new_work_hours': 0,
                                                            #'new_work_label': {label: 0 for label in all_labels}
                                                         }

    return member_stat


# In[25]:


def cardinfo_turn_to_dict(all_cards_info): # 把 card 转化成 dict
    cards_info = {}

    for card_info in all_cards_info:
        card_id = card_info['id']
        cards_info[card_id] = card_info
        del (cards_info[card_id]['id'])
 
    return cards_info # 最后的输出会把 id 变成 dict 里的 key，然后输入的参数中 id 就会被干掉。


# In[26]:


def period_list(list_name): # 通过输入单个的 list_name，然后统计从那个时候到现在的个人工作时间
    list_id = fetch_list_id_by_board(list_name)
    id_list = []
    url = 'https://api.trello.com/1/boards/_BOARDID_/lists?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_BOARDID_", g_board_id)
    body = do_request(url)
    
    for i in body:
        id_list.append(i["id"])
        
    for item in body: # 这里没有 item 的异常处理
        if item["id"] == list_id[0]["id"]: 
            id_pos = id_list.index(item["id"]) # 写漏了 id_list 从哪儿来

    return id_list[3:id_pos+1]


# In[27]:


def period_stats(new_list): # 
    
    board_members = fetch_members_by_board()
    list_id = fetch_list_id_by_board(new_list)[0]["id"]

    available_cards_info = get_cards_info(list_id, board_members) # 要先拿到 list_id
    cards_info = cardinfo_turn_to_dict(available_cards_info) # 变成字典格式
    member_stat = generate_member_stat_from_cards_info(cards_info) # 拿到成员字典
    
    period_list_id = period_list(new_list)
    all_single_list = [] # 收集所有的 card_list 之后的 card_info
    for item in period_list_id:
        single_list = get_cards_info(item, board_members) # 每一个 single_list 都类似于一个 available_cards_info
        all_single_list.append(single_list) # 设计一个报错卡片提示 
    
    member_stat = generate_member_stat_from_cards_info(cards_info) # 这里也需要加上 board 的所有成员才可以，不然就报错了
    for item in all_single_list:  
        for i in item:
            try:
                member_name = i['member_name']
                member_stat[member_name]['actual_hours']  += i['actual_hours']

            except KeyError as e: # 会出现 none 的情况 xueyuwei
                print("KeyError" + str(e) + " in " + i["card_name"]) 
    
    return member_stat


# In[56]:





# In[44]:


def week_list(): # 返回一个 doing 之后的 list_id
    id_list = []
    url = 'https://api.trello.com/1/boards/_BOARDID_/lists?key=_APP_KEY_&token=_TOKEN_'
    url = basic_replace(url)
    url = url.replace("_BOARDID_", g_board_id)
    body = do_request(url)

    for i in body:
        id_list.append(i["id"])
        
    return id_list[3]


# In[64]:



def single_list_stats(): # 单独一个 list 的工作时间统计 时间段统计不会用到
    list_id = week_list()
    board_members = fetch_members_by_board()
    
    available_cards_info = get_cards_info(list_id, board_members) # 要先拿到 list_id
    cards_info = cardinfo_turn_to_dict(available_cards_info) # 变成字典格式
    member_stat = generate_member_stat_from_cards_info(cards_info)
    
    for item in get_cards_info(list_id, board_members):
        member_name = item['member_name']
        member_stat[member_name]['actual_hours'] += item['actual_hours']
        
    return member_stat


# In[65]:


def bar_chart():
    
    single_list = single_list_stats()
    x=np.arange(len(single_list)) # 柱状图在横坐标上的位置
    y1=[40] 
    while len(y1) < len(x):
        y1.append(40)

    y2 = []
    for i in single_list.values():
        y2.append(i["actual_hours"])

    bar_width=0.2 #设置柱状图的宽度
    tick_label = single_list.keys()

    for a, b in enumerate(y1):
        plt.text(a, b, '%s' % b, ha='center', va='bottom')
    for a, b in enumerate(y2):
        plt.text(a, b, '%s' % b, ha='center', va='bottom') # 暂时没整明白这个 '%s' 是干啥的

    #绘制并列柱状图
    plt.bar(x,y1,bar_width,color='deepskyblue',label='标准时间')
    plt.bar(x+bar_width,y2,bar_width,color='orange',label='实际时间')

    plt.title("周工作量统计")
    plt.legend()#显示图例，即label
    plt.xticks(x+bar_width/2,tick_label)#显示x坐标轴的标签,即tick_label,调整位置，使其落在两个直方图中间位置?
    # plt.show()

    plt.savefig('work_hours_chart.png')
    print('------------> Save the bar chart successfully.')


# In[143]:


import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart



def addimg(src, imgid):
    fp = open(src, 'rb')
    msgImage = MIMEImage(fp.read())
    msgImage['Content-Type'] = 'application/octet-stream' # 设置为二进制流
    msgImage['Content-Disposition'] = 'attachment;filename="work_hours_chart.png"' #设置附件头，添加文件名
    
    fp.close()
    msgImage.add_header('Content-ID', imgid)
    return msgImage


# In[209]:


def send_mail():
    msg = MIMEMultipart('related')
    msgtext = MIMEText("""
    Dear Manager, 

    Here are workload statistics in this week, which is placed in the attachment.

    Best,
    Chenxi

    """, 'plain', 'utf-8')

    week_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #设置服务器所需信息
    mail_host = 'smtp.exmail.qq.com'  
    mail_user = 'chenxi.li@covenantsql.io'  
    mail_pass = 'qneBK9cjcEF5g34Q'  #密码(部分邮箱为授权码) 
    sender = 'chenxi.li@covenantsql.io'  #邮件发送方邮箱地址
    receivers = ['769087687@qq.com']  

    msg['Subject'] = 'Workload Statistics in {0}'.format(week_time)  #邮件主题
    msg['From'] = "Chenxi Li" #发送方信息
    msg['To'] = receivers[0]  #接受方信息 

    msg.attach(msgtext)
    msg.attach(addimg("work_hours_chart.png", "weekly"))

    try:
        smtpObj = smtplib.SMTP() #连接到服务器
        smtpObj.connect(mail_host,25)#登录到服务器
        smtpObj.login(mail_user,mail_pass)  #发送
        smtpObj.sendmail(
            sender,receivers,msg.as_string()) #退出

        smtpObj.quit() 
        print('Mail is send successfully')
    except smtplib.SMTPException as e: #打印错误
        print('error',e) 


# In[214]:


def main():
    bar_chart()
    send_mail()

if __name__ == '__main__':
    main()






# ## 单个 list 测试
# - 查看每个卡片 actual_hours 是否准确
# - 查看求和之后整个 list 的 actual hours 是否准确

# 工作流程：
# 先做 demo，然后再根据情况来改
# 
# - 1. 数据清理和统计
#     - 正则表达式能否判定，需要修改 用了 split 来统计
#     - list name 需要判定方式修改
#     - 统计出个人在每一个 list 上的工作时间，需要理清那些 hours 的逻辑
#     - save json 和完成新增卡片的统计
# - 2. 时间段统计，通过直接输入日期，然后拿到从那个时间开始到现在的所有工作时间统计
# 
# 流程 0606：
# 
# - 1. 单个 list 的统计、可视化：研究是用之前作图的脚本还是自己写
# - 1.5 用 python 发邮件
# - 2. 定时任务，每周五晚
# - 3. 模块化脚本、自动邮件等
# - 4. 【】统计

# 进度：
# - 1. 修复正则对 [] 判断，拿到 list_id
# - 2. 换了一种统计 actual hours 的方式
# - 3. cardinfo_turn_to_dict 函数，save json 还没弄
# - 4. 统计一个 list 中每个人的工作时长（单周统计）
# 
# 进度 0606 
# - 1. 时间段统计 finished
# - 2. 抽样数据检查，抽几周试一下
# - 3. 修复了一点 bug，可以适用于 thunderDB 
# 
# 进度 0612
# - 1. 加入了最新一周的统计
# - 2. 可视化

# 
# 问题：
# - 1. plan hours 是啥，我们 trello 里好像没有？
# - 2. 有没有写 label 的要求或者习惯
#     - 和需求都不需要。
# - 3. 「CQL 10」这些怎么算得？要不要统计？
#     - OKR 要计算，但是放到之后
# - 4. 完成统计时间段是否也要用 save json
# - 5. pt 统计，之后还是要区分 plan hours 和 actual hours
# 
# 
# 问题 0606:
# - 1. list 是依据什么来排序的？这个属于异常处理，有可能是依据创建时间、有可能是在 board 里的顺序
# - 2. 

# 
# 0613 工作计划
# - wikipedia
# - 自动邮件






