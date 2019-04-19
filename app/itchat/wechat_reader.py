from threading import Thread,Timer
import itchat
import base64
from ..model.User import *
from .tool import Process_Wechat,WechatBaseData
from flask import Flask
from ..model import db
from datetime import datetime
import re,random

app = Flask(__name__)

# logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

#新建一个线程
thread = Thread()
# 是否登陆微信
isLoggedIn = False
welcome_list = []
chatroom_list=[]


#后台检查是否登录
def monitor_login(itchat,current_user,app):
    global isLoggedIn
    while 1:
        waiting_time = 0
        while not isLoggedIn:
            status = itchat.check_login()
            waiting_time += 1
            print(waiting_time)
            if status == '200':
                print ("status is 200!")
                isLoggedIn = True
            elif status == '201':
                print ("status is 201!")
                if isLoggedIn is not None:
                    print ('Please press confirm on your phone.')
                    isLoggedIn = None
            elif status != '408':
                break
            elif waiting_time == 5:
                raise Exception
        if isLoggedIn:
            print ("已经确认登陆了")
            break

    print ("==== here status is ", status)
    itchat.check_login()
    init_result = itchat.web_init()
    wechat_init = Process_Wechat(db=db,app=app,itchat=itchat,current_user=current_user)
    wechat_init.process_web_init(init_result)
    # process_web_init(init_result,current_user.id,app)
    global chatroom_list
    chatroom_list = itchat.originInstance.storageClass.chatroomList
    wechat_init.process_chatroom(chatroom_list)
    wechat_init.process_wechatuser(chatroom_list)
    global welcome_list
    welcome_list = wechat_init.load_welcomeinfo()


    # #检测成员变化
    # wechatdata = WechatBaseData(chatroom_list)
    # welcome_thread = Timer(interval=5,function=monitor_members, args=(itchat, wechatdata))
    # welcome_thread.start()



    itchat.show_mobile_login()
    # itchat.get_contact(True)
    itchat.start_receiving()
    itchat.run()



#回调函数
def Qr2Img(uuid, status, qrcode):
    global qr_img
    qr_img = base64.b64encode(qrcode).decode('utf-8')
    return qr_img

def get_qrimg(current_user,app):
    global thread
    global isLoggedIn
    uuid = itchat.get_QRuuid()
    itchat.get_QR(uuid=uuid, qrCallback=Qr2Img)
    #已经登陆微信
    if isLoggedIn:
        # wechat 掉线或者登出
        if not thread.is_alive():
            isLoggedIn = False
            thread = Thread(target=monitor_login, args=(itchat, current_user, app))
            thread.start()
            return qr_img
        return None

    if thread.is_alive():
        return qr_img
    if not thread.is_alive():
        print('please Login')
    thread = Thread(target=monitor_login, args=(itchat,current_user,app))
    thread.start()

    return qr_img


def check_isLoggedIn():
    global isLoggedIn
    return isLoggedIn


#收到信息 入库
from itchat.content import *
@itchat.msg_register([TEXT],isGroupChat=True,isFriendChat=False)
def receive_text(msg):

    global chatroom_list
    print(msg.text)
    print(msg)
    group = msg.get('User').get('UserName')
    username = msg.get('ActualUserName')
    nickname = msg.get('ActualNickName')
    info_nickname = msg.get('User').get('Self').get('NickName')

    text = msg.text
    create_time = msg.get('CreateTime')
    # 消息写库
    with app.app_context():
        group_record = Wechat_group.query.filter_by(username=group).first()
        info_record = Wechat_info.query.filter_by(nickname=info_nickname).first()
        if group_record:
            print(group_record.id)
            print(username)
            user_record = Wechat_user.query.filter_by(wechat_group_id=group_record.id,username=username).first()
            msg_record = Wechat_message(wechat_user_id=user_record.id,message=text,
                                        createtime=datetime.fromtimestamp(create_time),
                                       wechat_info_id=info_record.id)

            db.session.add(msg_record)
            db.session.commit()


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
    else: return

    # 坑  不加这段代码 search_friends总会出错,update_friend对search_friend有影响?看看底层代码
    for member in itchat.update_chatroom(group_name).get('MemberList'):
        if member.get('NickName') == at_name:
            username= member.get('UserName')
            friend =itchat.update_friend(userName=username)

    friend = itchat.search_friends(name=at_name)
    print(itchat.search_friends(name=at_name))
    at_name = friend[0].get('NickName')

    global welcome_list
    # 随机发送欢迎消息
    filtered_list = list(filter(lambda x: x[0]==group_name,welcome_list))
    print(filtered_list)
    if len(filtered_list)>1:
        random.shuffle(filtered_list)
    for username,content in filtered_list:
        if username == group_name:
            res = '@'+at_name+'  '+content
            return res




# 设置入群自动欢迎
# def monitor_members(itchat,wechatdata):
#
#     chatroom_data = wechatdata.room_member_count
#     print('monitor_members',chatroom_data)
#     for username,count in chatroom_data.items():
#         room_info = itchat.update_chatroom(userName=username)
#         membercount = room_info.get('MemberCount')
#         print(count,'count')
#         print(membercount,'membercount')
#
#         print(welcome_list)
#         if int(membercount) > int(count):
#             for usr,content in welcome_list:
#                 if usr == username:
#                     itchat.send(content,toUserName=username)
#
#         wechatdata.room_member_count[username]=membercount
#
#     #定时任务需要重复启动timer 达到定时循环
#     welcome_thread = Timer(interval=10,function=monitor_members, args=(itchat, wechatdata))
#     welcome_thread.start()
#
#
# def monitor_adv():
#     pass
#
# def monitor_keyword():
#     pass
#
