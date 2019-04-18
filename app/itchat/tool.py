from app.model import *
from app.model.User import Wechat_info,Wechat_group,Wechat_message,Wechat_user,Welcome_info
from  logging import getLogger,INFO
logger = getLogger(__name__)
logger.setLevel(INFO)



class Process_Wechat(object):

    def __init__(self,db,app,current_user,itchat):
        '''

        :param db:database handler
        :param app: flask app
        :param current_user: deepcopy of current user
        :param itchat: itchat instance
        '''
        self.app = app
        self.current_user = current_user
        self.db = db
        self.itchat = itchat
        self.model_wechat_info = Wechat_info
        self.model_wechat_group = Wechat_group
        self.model_wechat_user = Wechat_user
        self.model_wechat_message = Wechat_message


    def process_web_init(self,dict):
        '''

        :param dict: itchat.web_init() results
        :return:
        '''
        wechat_user=dict.get('User')
        self.wechat_info_nickname = wechat_user.get('NickName')
        self.wechat_info_sex = wechat_user.get('Sex')
        self.wechat_info_uin = wechat_user.get('Uin')
        self.wechat_info_username = wechat_user.get('UserName')
        self.wechat_info_headimgurl = wechat_user.get('HeadImgUrl')
        self.wechat_info_remarkname = wechat_user.get('RemarkName', u'没有')
        self.wechat_info_signature = wechat_user.get('Signature')

        with self.app.app_context():
            user_record = self.model_wechat_info.query.filter_by(uin=self.wechat_info_uin).first()

            if user_record:
                user_record.nickname,user_record.sex = self.wechat_info_nickname, self.wechat_info_sex
                user_record.username,user_record.headimgurl = self.wechat_info_username, self.wechat_info_headimgurl
                user_record.signature,user_record.remarkname = self.wechat_info_signature, self.wechat_info_remarkname

            if not user_record:
                info = self.model_wechat_info(uin=self.wechat_info_uin, username=self.wechat_info_username,
                                   nickname=self.wechat_info_nickname, headimgurl=self.wechat_info_headimgurl,
                                   remarkname=self.wechat_info_remarkname,
                                   sex=self.wechat_info_sex, signature=self.wechat_info_signature, status=1,
                                   admin_user_info_id=self.current_user.get_id())
                self.db.session.add(info)
            try:
                self.db.session.commit()
                try:
                    self.wechat_info_id = info.id
                except:
                    self.wechat_info_id = user_record.id
                logger.info('**************************{}'.format(self.wechat_info_id))
            except Exception as e:
                print(e)
                logger.info('wechat_info提交失败')

    def _initialize(self,dbmodel,uin):
        # ?????初始化时判断该用户api返回信息和数据库历史中的变化
        pass

    def process_chatroom(self,chatroom_list):
        with self.app.app_context():
            wechat_group_wechat_info_id = self.model_wechat_info.query.get(self.wechat_info_id)

            for chatroom in chatroom_list:
                nickname = chatroom.get('NickName')
                username = chatroom.get('UserName')
                remarkname = chatroom.get('RemarkName')
                membercount = chatroom.get('MemberCount')
                isowner = True if chatroom.get('IsOwner') == '1' else False

                #判断是否存在，存在则更新
                group_record = self.model_wechat_group.query.filter_by(nickname=nickname).first()
                if group_record:
                    group_record.username, group_record.remarkname, group_record.membercount = username, remarkname, membercount
                    self.db.session.add(group_record)
                    continue
                group=self.model_wechat_group(wechat_info_id=wechat_group_wechat_info_id.id,username=username,
                                              nickname=nickname,remarkname=remarkname,
                                              membercount=membercount,isowner=isowner)
                self.db.session.add(group)
                print(group)
            try:
                self.db.session.commit()
            except Exception as e:
                print(e)
                logger.info('wechat_group提交失败')

    def process_wechatuser(self,chatroom_list):
        '''

        :param chatroom_list:
        :return:
        '''
        with self.app.app_context():
            for chatroom in chatroom_list:
                chatroom_username = chatroom.get('UserName')
                chatroom_nickname = chatroom.get('NickName')
                #先取群nickname,查库返回query对象
                wechat_group_id = self.model_wechat_group.query.filter_by(nickname=chatroom_nickname).first()
                chatroom_info = self.itchat.update_chatroom(userName=chatroom_username)
                memberlist = chatroom_info.get('MemberList')
                for member in memberlist:
                    username = member.get('UserName')
                    nickname = member.get('NickName')
                    displayname = member.get('DisplayName')

                    # 判断该用户名是否存在，存在则更新
                    weuser_record = self.model_wechat_user.query.filter_by(nickname=nickname,wechat_group_id=wechat_group_id.id).first()
                    if weuser_record:
                        weuser_record.username,weuser_record.remarkname = username, displayname
                        self.db.session.add(weuser_record)
                        continue

                    we_user = self.model_wechat_user(username=username, nickname=nickname,
                                                     remarkname=displayname,wechat_group_id=wechat_group_id.id,
                                                     wechat_info_id=self.wechat_info_id)
                    self.db.session.add(we_user)

                try:
                    self.db.session.commit()
                except Exception as e:
                    print(e)
                    logger.info('wechat_user提交失败')


    def load_black_white_list(self):
        with self.app.app_context():
            user_record = User.query.get(self.current_user.get_id())
            user_record


# def process_web_init(dict,current_user,app):
#
#     wechat_user = dict.get('User')
#     wechat_info_nickname = wechat_user.get('NickName')
#     sex = wechat_user.get('Sex')
#     uin = wechat_user.get('Uin')
#     print(type(uin))
#     username = wechat_user.get('UserName')
#     headimgurl = wechat_user.get('HeadImgUrl')
#     remarkname = wechat_user.get('RemarkName',u'没有')
#     signature = wechat_user.get('Signature')
#     print(signature)
#     with app.app_context():
#
#         print(current_user)
#         info = Wechat_info(uin=uin,username=username,nickname=wechat_info_nickname,headimgurl=headimgurl,remarkname=u'没有',
#                     sex=sex,signature='abc',status=1)
#         print(info)
#         db.session.add(info)
#         try:
#             db.session.commit()
#         except Exception as e:
#             print(e)
#             logger.info('wechat_info提交失败')
#
# #
# # def update_chatroom():
# def process_chatroom(chatroom_list,app):
#     with app.app_context():
#         Wechat_info.query.filter(nickname=wechat_info_nickname)
#         for chatroom in chatroom_list:
#             nickname = chatroom.get('NickName')
#             username = chatroom.get('UserName')
#             remarkname = chatroom.get('RemarkName')
#             membercount = chatroom.get('MemberCount')
#             isowner = True if chatroom.get('IsOwner')=='1' else False
#             wechat_group()
#
#
#     id = db.Column(db.Integer,primary_key=True,autoincrement=True)
#     wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))
#     username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
#     nickname = db.Column(db.String(255), comment="昵称")
#     remarkname = db.Column(db.String(255),comment="备注名")
#     membercout =db.Column(db.SMALLINT,comment='群内人数')
#     isowner = db.Column(db.BOOLEAN(),comment='是否群主')
#     time_group_sending_id = db.Column(db.Integer,db.ForeignKey('timing_group_sending.id'))
#
#     users = db.relationship('Wechat_user',backref=db.backref('group'))
#     welcome_infos = db.relationship('Welcome_info',backref=db.backref('group'))
#     auto_replies = db.relationship('Auto_reply',backref = db.backref('group'))

