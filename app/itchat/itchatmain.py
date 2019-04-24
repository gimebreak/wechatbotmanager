import itchat
import base64
from ..model.User import *
from .tool import Process_Wechat,WechatBaseData
from flask import Flask
from ..model import db
from datetime import datetime
import re,random
from time import sleep
from .base import BaseProcess
from itchat.content import *

app = Flask(__name__)

process = BaseProcess(app=app,itchat=itchat,db=db)


@itchat.msg_register([NOTE],isGroupChat=True,isFriendChat=False)
def receive_note(msg):
    text = msg.text
    print(msg)
    print(msg.text)
    print(msg.user)
    group_name = msg.get('FromUserName')
    reqr = re.compile('通过扫描"(.*?)".*?二维码')
    retog = re.compile('邀请"(.*?)"加入了群聊')

    if reqr.search(text):
        at_name = reqr.search(text).group(1)
    elif retog.search(text):
        at_name = retog.search(text).group(1)
    else:
        return

    unknown =None
    # 坑  不加这段代码 search_friends总会出错,update_friend对search_friend有影响?看看底层代码
    for member in itchat.update_chatroom(group_name).get('MemberList'):
        if member.get('NickName') == at_name:
            print('in the member loop')
            username = member.get('UserName')
            friend = itchat.update_friend(userName=username)
            unknown=member.get('NickName')


    friend = itchat.search_friends(name=at_name)
    try:
        at_name = friend[0].get('NickName')
    except Exception as e:
        print(e)
        at_name = unknown
    # 随机发送欢迎消息
    global process
    filtered_list = list(filter(lambda x: x[0] == group_name, process.welcome_list))
    print(filtered_list)
    if len(filtered_list) > 1:
        random.shuffle(filtered_list)
    for username, content in filtered_list:
        if username == group_name:
            res = '@' + at_name + '  ' + content
            return res



@itchat.msg_register([TEXT],isGroupChat=True,isFriendChat=False)
def receive_text(msg):
    global process
    # 过滤函数
    def _msgfilter(ntf,uncs,kw):
        if username not in uncs:
            for k in kw:
                rc = re.compile('.*?('+k+').*?')
                print(rc)
                res = rc.findall(msg.text)
                print(res)
                if res:
                    for g in ntf:
                        sleep(random.randrange(1,4))
                        itchat.send('{}在{}群里说了:{}'.format(nickname,group_nickname,msg.text),toUserName=g)
                    break

    # 暂未开放全部回复
    def _auto_reply(rule):
        for tp,gp,kw,rc,en,in rule:
            if group == gp.username:
                if en==1:
                    rcom = re.compile('.*?('+kw+').*?')
                    res = rcom.findall(msg.text)
                    if res:
                        sleep(random.randrange(1,4))
                        itchat.send(rc,toUserName=gp.username)



    print(msg.text)
    print(msg)
    try:
        group = msg.get('User').get('UserName')
        group_nickname = msg.get('User').get('NickName')
        username = msg.get('ActualUserName')
        nickname = msg.get('ActualNickName')
        info_nickname = msg.get('User').get('Self').get('NickName')
    except AttributeError:
        print("获取信息失败")
        return

    text = msg.text
    create_time = msg.get('CreateTime')
    # 消息写库
    with app.app_context():
        group_record = WechatGroup.query.filter_by(username=group).first()
        info_record = WechatInfo.query.filter_by(nickname=info_nickname).first()
        if group_record:
            user_record = WechatUser.query.filter_by(wechat_group_id=group_record.id,username=username).first()
            msg_record = WechatMessage(wechat_user_id=user_record.id,message=text,
                                        createtime=datetime.fromtimestamp(create_time),
                                       wechat_info_id=info_record.id)

            db.session.add(msg_record)
            db.session.commit()
    print(process.rule)
    ad_notifs, ad_uncensor, ad_keywords =process.rule.get('ad_rule')
    _msgfilter(ad_notifs, ad_uncensor, ad_keywords)
    k_notifs, k_uncensor, k_keyword = process.rule.get('keyword_rule')
    _msgfilter(k_notifs, k_uncensor, k_keyword)
    auto_reply_rule = process.auto_replies
    _auto_reply(auto_reply_rule)



