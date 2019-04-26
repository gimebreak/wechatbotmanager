import itchat
import base64
from ..model.model import *
from .tool import Process_Wechat,WechatBaseData,logger
from hashlib import md5
from datetime import datetime
import re,random
from time import sleep,time
from threading import Thread
from itchat.content import *



def _hotload_address():
    m1 = md5()
    m1.update(str(time()).encode('utf8'))
    return m1.hexdigest()

class TimeRunoutError(BaseException):
    pass

class BaseProcess(object):
    user_list={}

    def __init__(self,app,itchat,db):
        self.app = app
        self.itchat = itchat
        self.db = db
        self.thread = Thread()
        self.welcomeList = []
        self.chatroomList = []
        self.rule = {'ad_rule':[],'keyword_rule':[]}
        self.qr_img = 0
        self.auto_replies = []
        self.isLoggedIn = False



    #初始化调用 ,更新current_user. 必须
    def __call__(self, current_user):
        self.current_user = current_user

        if self.current_user.get_id() not in self.user_list.keys():
            self.user_list.update({self.current_user.get_id():self})

        def _qrtrans(uuid, status, qrcode):
            self.qr_img = base64.b64encode(qrcode).decode('utf-8')
            logger.info('QR code downloaded,encoded as base64')

        def _entry(self,current_user,app):
            if not self.isLoggedIn:
                load_status = self.itchat.load_login_status('data/itchat{}.pk1'.format(current_user.get_id()))
                logger.info(load_status)

                if load_status.get('BaseResponse').get('Ret') == 0:
                    logger.info('{}hotload success'.format(current_user.name))
                    self.isLoggedIn = True
                    self.thread = Thread(target=self.readygo,args=(True,))
                    self.thread.start()
                    self.itchat.dump_login_status('data/itchat{}.pk1'.format(current_user.get_id()))
                    return None

                uuid = itchat.get_QRuuid()
                itchat.get_QR(uuid=uuid, qrCallback=_qrtrans)
                # actions taken when hotload passed

                #未扫描二维码刷新，不再开启新线程监控
                if self.thread.is_alive() and self.qr_img !=0 :
                    return self.qr_img

                if not self.thread.is_alive():
                    logger.info('please Login')
                self.thread = Thread(target=self.monitor_login)
                self.thread.start()

                return self.qr_img
            # 已经登陆微信
            if self.isLoggedIn:

                # wechat 掉线或者登出
                if not self.thread.is_alive():
                    print('threadalive3:', self.thread.is_alive())
                    self.isLoggedIn = False
                    uuid = itchat.get_QRuuid()
                    itchat.get_QR(uuid=uuid, qrCallback=_qrtrans)
                    self.thread = Thread(target=self.monitor_login)
                    self.thread.start()
                    return self.qr_img
                return None
        return _entry(self,self.current_user,self.app)

    def monitor_login(self):
        try:
            while 1:
                waiting_time = 0
                while not self.isLoggedIn:
                    status = self.itchat.check_login()
                    waiting_time += 1
                    if status == '200':
                        self.isLoggedIn = True
                        print("status is 200!")

                    elif status == '201':
                        print("status is 201!")
                        if self.isLoggedIn is not None:
                            print('Please press confirm on your phone.')
                            self.isLoggedIn = None
                    elif status != '408':
                        break
                    elif waiting_time == 5:
                        raise TimeRunoutError
                if self.isLoggedIn:
                    print('已经确认登陆')
                    break
        except TimeRunoutError as e:
            logger.warning('时间超过,二维码失效')
            return

        print("==== here status is ", status)
        self.itchat.check_login()
        self.readygo()


    def readygo(self,hotload=False):
        init_result = self.itchat.web_init()
        self.itchat.dump_login_status('data/itchat{}.pk1'.format(self.current_user.get_id()))
        self.wechat_init = Process_Wechat(db=self.db, app=self.app,
                                     itchat=self.itchat, current_user=self.current_user)
        self.wechat_init.process_web_init(init_result)
        self.chatroomList = self.itchat.originInstance.storageClass.chatroomList
        self.wechat_init.process_chatroom(self.chatroomList)
        self.wechat_init.process_wechatuser(self.chatroomList)
        self.welcome_list = self.wechat_init.load_welcomeinfo()
        ad_notifs, ad_uncensor, ad_keywords = self.wechat_init.load_adv_rule()
        self.rule ={'ad_rule':[],'keyword_rule':[]} #清零
        self.rule['ad_rule'].extend([ad_notifs, ad_uncensor, ad_keywords])
        k_notifs, k_uncensor, k_keyword = self.wechat_init.load_keyword_rule()
        self.rule['keyword_rule'].extend([k_notifs, k_uncensor, k_keyword])
        print('rule', self.rule)

        self.auto_replies = self.wechat_init.load_auto_reply()
        self.register()
        itchat.show_mobile_login()
        itchat.get_contact(True)
        if not hotload:
            itchat.start_receiving()
        itchat.run()


    def register(self):

        # @itchat.msg_register(INCOME_MSG)
        # def income(msg):
        #     print(msg)

        @itchat.msg_register([NOTE], isGroupChat=True, isFriendChat=False)
        def receive_note(msg):
            print(msg.text)
            print(msg)
            def _add_parent(parent,groupname,username,nickname,remarkname):
                with self.app.app_context():
                    group = WechatGroup.query.filter_by(username=groupname).first()
                    # 若没在登入时加载，则重新加载该群
                    try:
                        if not group:
                            chatroom = itchat.update_chatroom(groupname)
                            chatroom = itchat.search_chatrooms(userName=groupname)
                            self.wechat_init.fix_group([chatroom])
                            self.wechat_init.fix_user([chatroom])
                            #再次加载group
                            group = WechatGroup.query.filter_by(username=groupname).first()

                    except Exception as e:
                        logger.error('群信息未加载成功')

                    parent = WechatUser.query.filter_by(nickname=parent.strip('"'),wechat_group_id=group.id).first()
                    user = WechatUser.query.filter_by(wechat_group_id=group.id,username=username).first()
                    if user:
                        weuser=user
                        weuser.parent_id=parent.id
                    else:
                        weuser = WechatUser(wechat_group_id=group.id,username=username,nickname=nickname,
                               remarkname=remarkname,wechat_info_id=group.info.id,parent_id=parent.id)
                    self.db.session.add(weuser)
                    self.db.session.commit()

            def _get_newcomer(msg,at_name):
                groupname = msg.get('FromUserName')
                g = itchat.update_chatroom(userName=groupname)

                try:
                    for m in g.get('MemberList'):
                        m_username = m.get('UserName')
                        m_nickname = m.get('NickName')
                        m_remarkname = m.get('DisplayName')
                        if m_nickname == at_name:
                            return m_username,m_nickname,m_remarkname
                except:
                    logger.info('获取新人:{} 的信息失败失败'.format(at_name))
                    return '','',''
                return '','',''

            def _get_name(msg):
                text = msg.text
                group_name = msg.get('FromUserName')
                parent_username = msg.get('ActualNickName')
                reqr = re.compile('(.*?)通过扫描"(.*?)".*?二维码')
                retog = re.compile('(.*?)邀请"(.*?)"加入了群聊')
                if reqr.search(text):
                    if reqr.findall(text)[0][0] == '你':
                        parent = parent_username
                        at_name = reqr.search(text).group(2)
                    else:
                        parent = reqr.search(text).group(1)
                        at_name = reqr.search(text).group(2)
                    return parent,at_name
                elif retog.search(text):
                    if retog.findall(text)[0][0] == '你':
                        parent = parent_username
                        at_name = retog.search(text).group(2)
                    else:
                        parent = retog.search(text).group(1)
                        at_name = retog.search(text).group(2)
                    return parent, at_name
                else:
                    return None,None

            parent,at_name = _get_name(msg)
            print(at_name,'at_name')

            if not at_name:
                return

            username, at_name, remarkname = _get_newcomer(msg,at_name)
            group_name = msg.get('FromUserName')

            if at_name !='':
                _add_parent(parent, group_name,username,at_name,remarkname)

            # 随机发送欢迎消息
            filtered_list = list(filter(lambda x: x[0] == group_name, self.welcome_list))
            print(filtered_list)
            if len(filtered_list) > 1:
                random.shuffle(filtered_list)
            for username, content in filtered_list:
                if username == group_name:
                    res = '@' + at_name + '  ' + content
                    return res

        @itchat.msg_register([TEXT], isGroupChat=True, isFriendChat=False)
        def receive_text(msg):
            # 过滤函数
            def _msgfilter(ntf, uncs, kw):
                if username not in uncs:
                    for k in kw:
                        rc = re.compile('.*?(' + k + ').*?')
                        print(rc)
                        res = rc.findall(msg.text)
                        print(res)
                        if res:
                            for g in ntf:
                                sleep(random.randrange(1, 4))
                                itchat.send('{}在{}群里说了:{}'.format(nickname, group_nickname, msg.text), toUserName=g)
                            break

            # 暂未开放全部回复
            def _auto_reply(rule):
                print(rule)
                for tp, gp, kw, rc, en, in rule:
                    if group == gp.username:
                        if en == 1:
                            rcom = re.compile('.*?(' + kw + ').*?')
                            res = rcom.findall(msg.text)
                            if res:
                                sleep(random.randrange(1, 4))
                                itchat.send(rc, toUserName=gp.username)
                                break

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
            with self.app.app_context():
                group_record = WechatGroup.query.filter_by(username=group).first()
                info_record = WechatInfo.query.filter_by(nickname=info_nickname).first()
                if group_record:
                    user_record = WechatUser.query.filter_by(wechat_group_id=group_record.id, username=username).first()
                    msg_record = WechatMessage(wechat_user_id=user_record.id, message=text,
                                               createtime=datetime.fromtimestamp(create_time),
                                               wechat_info_id=info_record.id)

                    db.session.add(msg_record)
                    db.session.commit()

            ad_notifs, ad_uncensor, ad_keywords = self.rule.get('ad_rule')
            _msgfilter(ad_notifs, ad_uncensor, ad_keywords)
            k_notifs, k_uncensor, k_keyword = self.rule.get('keyword_rule')
            _msgfilter(k_notifs, k_uncensor, k_keyword)
            auto_reply_rule = self.auto_replies
            _auto_reply(auto_reply_rule)