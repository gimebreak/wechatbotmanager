import itchat
import base64
from ..model.User import *
from .tool import Process_Wechat,WechatBaseData
from flask import Flask
from hashlib import md5
from datetime import datetime
import re,random
from time import sleep,time
from threading import Thread
import threading
from itchat.content import *

def _hotload_address():
    m1 = md5()
    m1.update(str(time()).encode('utf8'))
    return m1.hexdigest()


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

        def _entry(self,current_user,app):
            print(self.isLoggedIn,'self is loggedin')
            if not self.isLoggedIn:
                load_status = self.itchat.load_login_status('data/itchat{}.pk1'.format(current_user.get_id()))
                print('threadalive1:', threading.active_count())
                print(self.thread.is_alive())
                print(self.qr_img,'qr_img')
                print(load_status)
                if load_status.get('BaseResponse').get('Ret') == 0:
                    self.isLoggedIn = True
                    self.thread = Thread(target=self.readygo)
                    self.thread.start()
                    self.itchat.dump_login_status('data/itchat{}.pk1'.format(current_user.get_id()))
                    print('threadalive2:', threading.active_count())
                    return None
                uuid = itchat.get_QRuuid()
                itchat.get_QR(uuid=uuid, qrCallback=_qrtrans)

                if self.thread.is_alive() and self.qr_img !=0 :
                    return self.qr_img

                if not self.thread.is_alive():
                    print('please Login')
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

        print('threadalive5:', threading.active_count())
        return _entry(self,self.current_user,self.app)

    def monitor_login(self):
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
                    raise Exception
            if self.isLoggedIn:
                print('已经确认登陆')
                break
        print("==== here status is ", status)
        self.itchat.check_login()
        self.readygo()


    def readygo(self):
        init_result = self.itchat.web_init()
        self.itchat.dump_login_status('data/itchat{}.pk1'.format(self.current_user.get_id()))
        wechat_init = Process_Wechat(db=self.db, app=self.app,
                                     itchat=self.itchat, current_user=self.current_user)
        wechat_init.process_web_init(init_result)
        self.chatroomList = self.itchat.originInstance.storageClass.chatroomList
        wechat_init.process_chatroom(self.chatroomList)
        wechat_init.process_wechatuser(self.chatroomList)
        self.welcome_list = wechat_init.load_welcomeinfo()
        ad_notifs, ad_uncensor, ad_keywords = wechat_init.load_adv_rule()
        self.rule ={'ad_rule':[],'keyword_rule':[]} #清零
        self.rule['ad_rule'].extend([ad_notifs, ad_uncensor, ad_keywords])
        k_notifs, k_uncensor, k_keyword = wechat_init.load_keyword_rule()
        self.rule['keyword_rule'].extend([k_notifs, k_uncensor, k_keyword])
        print('rule', self.rule)

        self.auto_replies = wechat_init.load_auto_reply()

        itchat.show_mobile_login()
        # itchat.get_contact(True)
        itchat.start_receiving()
        itchat.run()

