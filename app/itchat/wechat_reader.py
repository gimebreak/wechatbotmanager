from threading import Thread,Timer
import itchat
import base64
from ..model.User import *
from .tool import Process_Wechat,WechatBaseData
from flask import Flask
from ..model import db
from datetime import datetime
import re,random
from time import sleep

app = Flask(__name__)

# logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

#新建一个线程
thread = Thread()
# 是否登陆微信
isLoggedIn = False
welcome_list = []
chatroom_list=[]
rule={'ad_rule':[],'keyword_rule':[]}

#后台检查是否登录
def monitor_login(itchat,current_user,app):
    global isLoggedIn

    while 1:
        waiting_time = 0
        while not isLoggedIn:
            status = itchat.check_login()
            waiting_time += 1
            print(status)
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
    ready(app,itchat,current_user)
    # init_result = itchat.web_init()
    #
    # wechat_init = Process_Wechat(db=db,app=app,itchat=itchat,current_user=current_user)
    # wechat_init.process_web_init(init_result)
    # # process_web_init(init_result,current_user.id,app)
    # global chatroom_list
    # chatroom_list = itchat.originInstance.storageClass.chatroomList
    # wechat_init.process_chatroom(chatroom_list)
    # wechat_init.process_wechatuser(chatroom_list)
    # global welcome_list
    # welcome_list = wechat_init.load_welcomeinfo()
    #
    # # 加载过滤条件
    # ad_notifs, ad_uncensor, ad_keywords = wechat_init.load_adv_rule()
    # rule['ad_rule'].extend([ad_notifs,ad_uncensor,ad_keywords])
    # k_notifs, k_uncensor, k_keyword = wechat_init.load_keyword_rule()
    # rule['keyword_rule'].extend([k_notifs,k_uncensor,k_keyword])
    #
    # itchat.show_mobile_login()
    # # itchat.get_contact(True)
    # itchat.start_receiving()
    # itchat.run()

def ready(app,itchat,current_user):
    init_result = itchat.web_init()
    wechat_init = Process_Wechat(db=db, app=app, itchat=itchat, current_user=current_user)
    wechat_init.process_web_init(init_result)
    # process_web_init(init_result,current_user.id,app)
    global chatroom_list
    chatroom_list = itchat.originInstance.storageClass.chatroomList
    wechat_init.process_chatroom(chatroom_list)
    wechat_init.process_wechatuser(chatroom_list)
    global welcome_list
    welcome_list = wechat_init.load_welcomeinfo()

    # 加载过滤条件
    ad_notifs, ad_uncensor, ad_keywords = wechat_init.load_adv_rule()
    rule['ad_rule'].extend([ad_notifs, ad_uncensor, ad_keywords])
    k_notifs, k_uncensor, k_keyword = wechat_init.load_keyword_rule()
    rule['keyword_rule'].extend([k_notifs, k_uncensor, k_keyword])
    print('rule',rule)

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
    import threading

    if not isLoggedIn:
        #load_status 会开启一个线程
        load_status = itchat.load_login_status('itchat.pkl')
        print('threadalive1:', threading.active_count())
        #服务器接受hotreload,开始数据的初始化
        if load_status.get('BaseResponse').get('Ret') == 0:
                isLoggedIn = True
                thread = Thread(target=ready, args=(app, itchat, current_user))
                thread.start()
                itchat.dump_login_status('itchat.pkl')
                print('threadalive2:', threading.active_count())
                return None

        uuid = itchat.get_QRuuid()
        itchat.get_QR(uuid=uuid, qrCallback=Qr2Img)

        if thread.is_alive():
            return qr_img
        if not thread.is_alive():
            print('please Login')
        thread = Thread(target=monitor_login, args=(itchat,current_user,app))
        thread.start()
        return qr_img
    #已经登陆微信
    if isLoggedIn:
        # wechat 掉线或者登出
        if not thread.is_alive():
            print('threadalive3:', thread.is_alive())
            isLoggedIn = False
            thread = Thread(target=monitor_login, args=(itchat, current_user, app))
            thread.start()
            return qr_img
        return None



def check_isLoggedIn():
    global isLoggedIn
    return isLoggedIn


#收到信息 入库
from itchat.content import *
@itchat.msg_register([TEXT],isGroupChat=True,isFriendChat=False)
def receive_text(msg):
    # 过滤函数
    def msgfilter(ntf,uncs,kw):
        if username not in uncs:
            for k in kw:
                rc = re.compile('.*?('+k+').*?')
                print(rc)
                res = rc.findall(msg.text)
                print(res)
                if res:
                    for g in ntf:
                        print(g)
                        sleep(random.randrange(1,4))
                        itchat.send('{}在{}群里说了:{}'.format(nickname,group_nickname,msg.text),toUserName=g)
                    break

    global chatroom_list
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
            print(group_record.id)
            print(username)
            user_record = WechatUser.query.filter_by(wechat_group_id=group_record.id,username=username).first()
            msg_record = WechatMessage(wechat_user_id=user_record.id,message=text,
                                        createtime=datetime.fromtimestamp(create_time),
                                       wechat_info_id=info_record.id)

            db.session.add(msg_record)
            db.session.commit()

    ad_notifs, ad_uncensor, ad_keywords =rule.get('ad_rule')
    print(rule)
    print('this is rule*************')
    msgfilter(ad_notifs, ad_uncensor, ad_keywords)
    k_notifs, k_uncensor, k_keyword = rule.get('keyword_rule')
    msgfilter(k_notifs, k_uncensor, k_keyword)



#入群自动欢迎
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
    print(friend)
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


