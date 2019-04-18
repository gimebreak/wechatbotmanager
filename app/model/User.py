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
    infos = db.relationship('Wechat_info',
                            backref=db.backref('user'))

    def __str__(self):
        return self.email

class Timing_group_sending(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime())
    content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT, comment='1:功能启用,0:此功能暂停')

    groups = db.relationship('Wechat_group', backref=db.backref('timing_group_sending'))


#
class Wechat_info(db.Model):

    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    uin = db.Column(db.Integer,unique=True,comment='用户唯一标识符')
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255),comment="昵称")
    headimgurl = db.Column(db.String(255),comment="头像链接")
    remarkname = db.Column(db.String(255),comment="备注名")
    sex = db.Column(db.Integer,comment="性别，0-未设置（公众号、保密），1-男，2-女")
    signature = db.Column(db.String(255))
    admin_user_info_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    status=db.Column(db.Integer,comment='1:登陆;0:未登录')
    groups = db.relationship('Wechat_group',backref=db.backref('info'))
    users = db.relationship('Wechat_user',backref=db.backref('info'))
    msgs = db.relationship('Wechat_message',backref=db.backref('info'))


    def __repr__(self):
        return self.nickname

class Wechat_group(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255), comment="昵称")
    remarkname = db.Column(db.String(255),comment="备注名")
    membercount =db.Column(db.SMALLINT,comment='群内人数')
    isowner = db.Column(db.BOOLEAN(),comment='是否群主')
    time_group_sending_id = db.Column(db.Integer,db.ForeignKey('timing_group_sending.id'))
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))

    users = db.relationship('Wechat_user',backref=db.backref('group'))
    welcome_infos = db.relationship('Welcome_info',backref=db.backref('group'))
    auto_replies = db.relationship('Auto_reply',backref = db.backref('group'))


    def __repr__(self):
        return self.nickname

# 群内用户
class Wechat_user(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    username = db.Column(db.String(255),comment="用户名称，一个@为好友，两个@为群组")
    nickname = db.Column(db.String(255), comment="昵称")
    remarkname = db.Column(db.String(255),comment="备注名")
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))

    msgs = db.relationship('Wechat_message',backref=db.backref('wechatuser'))
    # group = db.relationship('wechat_group', backref=db.backref('users'))
    def __repr__(self):
        return self.nickname
#
#
class Welcome_info(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    type = db.Column(db.SMALLINT,comment='1:message,0:pic_content')
    content = db.Column(db.Text)
    pic_url = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')
    #
class Auto_reply(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    type = db.Column(db.SMALLINT,comment='1:定向,0:全部')
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    keyword= db.Column(db.String(255))
    reply_content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')
#



class Immediate_group_sending(db.Model):

    id = db.Column(db.Integer,primary_key=True)

    # groups = db.Column()

    content = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')

class Wechat_message(db.Model):

    id = db.Column(db.Integer,primary_key=True)

    message = db.Column(db.Text)
    createtime = db.Column(db.DateTime())
    wechat_user_id = db.Column(db.Integer, db.ForeignKey('wechat_user.id'))
    wechat_info_id = db.Column(db.Integer,db.ForeignKey('wechat_info.id'))


class Favorate_message(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_message_id = db.Column(db.Integer, db.ForeignKey('wechat_message.id'))

class Adv_notification_group(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer, db.ForeignKey('wechat_group.id'))

class ADV_whitelist_user(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_user = db.Column(db.Integer,db.ForeignKey('wechat_user.id'))

class Adv_blacklist(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    keyword = db.Column(db.String(255))

class Keyword_notification_group(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))

class Keyword_whitelist_user(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    wechat_user_id = db.Column(db.Integer,db.ForeignKey('wechat_user.id'))

class keyword_blacklist(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    keyword = db.Column(db.String(255))

