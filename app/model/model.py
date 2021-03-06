from flask_security import UserMixin,RoleMixin
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    # users = db.relationship('User',backref=db.backref('role'))

    def __str__(self):
        return self.name

#坑 表的大小写，驼峰式写法的大写字母会转译为'_'
class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(255),)
    email = db.Column(db.String(255), unique=True,)
    password = db.Column(db.String(255),)
    active = db.Column(db.Boolean(),)
    confirmed_at = db.Column(db.DateTime())

    # role_id =db.Column(db.Integer, db.ForeignKey('role.id'))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    infos = db.relationship('WechatInfo',
                            backref=db.backref('user'))

    adv_notification_groups = db.relationship('AdvNotificationGroup',
                                              backref=db.backref('user'))
    adv_whitelist_users = db.relationship('AdvWhitelistUser',
                                          backref=db.backref('user'))
    adv_blacklist_keywords = db.relationship('AdvBlacklist',
                                          backref=db.backref('user'))
    keyword_notification_groups = db.relationship('KeywordNotificationGroup',
                                          backref=db.backref('user'))
    keyword_whitelist_users =  db.relationship('KeywordWhitelistUser',backref=db.backref('user'))
    keyword_blacklist = db.relationship('KeywordBlacklist',
                                          backref=db.backref('user'))


    def __str__(self):
        return self.email

class TimingGroupSending(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime())
    content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT, comment='1:功能启用,0:此功能暂停')

    groups = db.relationship('WechatGroup', backref=db.backref('timing_group_sending'))


#
class WechatInfo(db.Model):

    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    uin = db.Column(db.Integer,comment='用户唯一标识符')
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255),comment="昵称")
    headimgurl = db.Column(db.String(255),comment="头像链接")
    remarkname = db.Column(db.String(255),comment="备注名")
    sex = db.Column(db.Integer,comment="性别，0-未设置（公众号、保密），1-男，2-女")
    signature = db.Column(db.String(255))
    admin_user_info_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    status=db.Column(db.Integer,comment='1:登陆;0:未登录')
    groups = db.relationship('WechatGroup',backref=db.backref('info'))
    users = db.relationship('WechatUser',backref=db.backref('info'))
    msgs = db.relationship('WechatMessage',backref=db.backref('info'))


    def __repr__(self):
        return self.nickname

class WechatGroup(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255), comment="昵称")
    remarkname = db.Column(db.String(255),comment="备注名")
    membercount =db.Column(db.SMALLINT,comment='群内人数')
    isowner = db.Column(db.BOOLEAN(),comment='是否群主')
    time_group_sending_id = db.Column(db.Integer,db.ForeignKey('timing_group_sending.id'))
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))

    users = db.relationship('WechatUser',backref=db.backref('group'))
    welcome_infos = db.relationship('WelcomeInfo',backref=db.backref('group'))
    auto_replies = db.relationship('AutoReply',backref = db.backref('group'))
    adv_notification_groups = db.relationship('AdvNotificationGroup',
                                              backref=db.backref('group'))
    keyword_notification_groups = db.relationship('KeywordNotificationGroup',
                                              backref=db.backref('group'))


    def __repr__(self):
        return self.nickname

# 群内用户
class WechatUser(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255), comment="昵称")
    remarkname = db.Column(db.String(255),comment="备注名")
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))

    msgs = db.relationship('WechatMessage',
                           backref=db.backref('wechat_user'))
    adv_whitelist_users = db.relationship('AdvWhitelistUser',
                                          backref=db.backref('wechat_user'))

    keyword_whitelist_users = db.relationship('KeywordWhitelistUser',
                                          backref=db.backref('wechat_user'))

    # group = db.relationship('wechat_group', backref=db.backref('users'))
    def __repr__(self):
        return self.nickname
#
#

class WelcomeInfo(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    type = db.Column(db.SMALLINT,comment='1:message,0:pic_content')
    content = db.Column(db.Text)
    pic_url = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')
    #
class AutoReply(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    type = db.Column(db.SMALLINT,comment='1:定向,0:全部')
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    keyword= db.Column(db.String(255))
    reply_content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')
#

class WechatMessage(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    message = db.Column(db.Text)
    createtime = db.Column(db.DateTime())
    wechat_user_id = db.Column(db.Integer, db.ForeignKey('wechat_user.id'))
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))
    favorates = db.relationship('FavorateMessage',backref=db.backref('message'))

class ImmediateGroupSending(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')

class FavorateMessage(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_message_id = db.Column(db.Integer, db.ForeignKey('wechat_message.id'))


class AdvNotificationGroup(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    wechat_group_id = db.Column(db.Integer, db.ForeignKey('wechat_group.id'))
#
class AdvWhitelistUser(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_user_id = db.Column(db.Integer,db.ForeignKey('wechat_user.id'))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))

#
class AdvBlacklist(db.Model):
   # 广告关键字设置
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    keyword = db.Column(db.String(255))

class KeywordNotificationGroup(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    # user = db.relationship('User',backref=('keyword_notification_groups'))
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    # group = db.relationship('WechatGroup',backref=('keyword_notification_groups'))

class KeywordWhitelistUser(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_user_id = db.Column(db.Integer,db.ForeignKey('wechat_user.id'))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
#
class KeywordBlacklist(db.Model):
    # interested关键字设置
    id = db.Column(db.Integer,primary_key=True)
    keyword = db.Column(db.String(255))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))



