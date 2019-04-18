from threading import Thread
import itchat as itchat
import base64
from ..model.User import *
from .tool import Process_Wechat
from flask import Flask
from ..model import db
from datetime import datetime

app = Flask(__name__)

# logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

#新建一个线程
thread = Thread()
# 是否登陆微信
isLoggedIn = False

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

    chatroom_list = itchat.originInstance.storageClass.chatroomList
    print(chatroom_list)
    wechat_init.process_chatroom(chatroom_list)
    wechat_init.process_wechatuser(chatroom_list)
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
def receive(msg):
    print(msg.text)
    print(msg)
    group = msg.get('User').get('UserName')
    username = msg.get('ActualUserName')
    nickname = msg.get('ActualNickName')
    text = msg.text
    create_time = msg.get('CreateTime')
    with app.app_context():
        print(group)
        print(username)
        print(nickname)
        group_record = Wechat_group.query.filter_by(username=group).first()
        if group_record:
            print(group_record.id)
            print(username)
            user_record = Wechat_user.query.filter_by(wechat_group_id=group_record.id,username=username).first()
            msg_record = Wechat_message(wechat_user_id=user_record.id,message=text,createtime=datetime.fromtimestamp(create_time))
            db.session.add(msg_record)
            db.session.commit()

