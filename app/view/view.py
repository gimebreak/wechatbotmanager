from flask_admin.contrib import sqla
from flask import abort,redirect,url_for,request,jsonify
from flask_security import current_user
from flask_admin.base import expose
from flask_admin import babel
from flask_admin import AdminIndexView
from ..itchat.wechat_reader import get_qrimg
from . import bp
from ..itchat.wechat_reader import check_isLoggedIn,app
from copy import deepcopy
from ..model.User import *

class WeChatAdminView(AdminIndexView):

    def  __init__(self,name=None, category=None,
                 endpoint=None, url=None,
                 template='admin/index.html',
                 menu_class_name=None,
                 menu_icon_type=None,
                 menu_icon_value=None):
        super(WeChatAdminView,self).__init__(name or babel.lazy_gettext('Home'),
                                             category,
                                             endpoint or 'admin',
                                             '/admin' if url is None else url,
                                             'static',
                                             menu_class_name=menu_class_name,
                                             menu_icon_type=menu_icon_type,
                                             menu_icon_value=menu_icon_value)

        self._template = template

    @expose()
    def index(self):
        if not current_user.is_authenticated:
            self.render(self._template)
        cur_user=deepcopy(current_user)
        QRimg = get_qrimg(cur_user,app)
        print(QRimg)
        if QRimg ==None:
            return self.render(self._template)
        img_element = '<img id="qrimg" alt="Base64 encoded image" style="text-align: center" src="data:image/png;base64,{}"/>'.format(QRimg)

        return self.render(self._template,qrimg=img_element)





class BaseUserView(sqla.ModelView):

# 可用来自定义view逻辑
    # @expose('/')
    # def index_view(self):
    #     print('hello')
    #     return super(MyModelView,self).index_view()

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

    # 用户只能查看数据库中自己的微信信息
    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):

        count,query = super(BaseUserView,self).get_list(page, sort_column, sort_desc, search, filters,
                 execute=False, page_size=None)
        # 当前用户的infos
        user_record = User.query.get(current_user.get_id()).infos
        res = []
        # 当前model 过滤条件为用户info

        for info in user_record:
            res += query.from_self().filter_by(wechat_info_id=info.id).all()
        query = res

        print('get_list')
        print(count)

        return count,query


class GroupBasedView(sqla.ModelView):

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
                )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        count,query = super(GroupBasedView,self).get_list(page, sort_column, sort_desc, search, filters,
                 execute=False, page_size=None)

        user_record = User.query.get(current_user.get_id()).infos
        group_records = []
        res = []

        # 当前model 过滤条件为用户info
        for info in user_record:
            group_records += Wechat_group.query.filter_by(wechat_info_id=info.id).all()

        for group in group_records:
            res += query.from_self().filter_by(wechat_group_id=group.id).all()
        query = res

        return count,query




class SuperUserView(sqla.ModelView):

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user') or current_user.has_role('superuser')
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

class UserModelView(SuperUserView):
    # column_searchable_list=('first_name','last_name')
    column_searchable_list = ('name', 'email')
    column_list = ('id','name','email','roles')
    column_labels = {
        'id': u'序号',
        'name': u'用户名',
        'email': u'邮箱',
        'active': u'激活',
        'roles': u'角色'
    }


class WeChatGroupView(BaseUserView):
    column_list = ('id','info', 'username', 'nickname')
    column_labels = {
        'id': u'序号',
        'username': u'群名称',
        'nickname': u'昵称',
        'remarkname':u'备注名',
        'membercount':u'人数统计',
        'isowner':'是否群主',
        'info':'用户' ,
        'users':'成员',
        'welcome_infos':'欢迎语',
        'auto_replies':'自动回复',
        'timing_group_sending':'定时发送',
    }
    #内联模型: 只有one2many才可进行内联编辑
    # inline_models = (Wechat_user,)
    # form_columns = (Wechat_group.id,Wechat_group.users)

class WechatMsgView(BaseUserView):
    column_list = ('id','wechatuser','wechatuser.group.nickname','message','createtime')
    column_labels = {
        'id':u'序号',
        'wechatuser':u'微信名',
        'wechatuser.group.nickname': '所在群',
        'message':'消息内容',
        'createtime':'创建时间',

    }


class WechatUserView(BaseUserView):
    column_list = ('id', 'nickname','group', )
    column_labels = {
        'id': u'序号',
        'nickname': u'微信名',
        'group':u'所属群',
    }

class WechatWelcomeInfoView(GroupBasedView):
    column_list = ('id', 'group','type','content','pic_url','enabled' )
    column_labels = {
        'id': u'序号',
        'group':u'所属群',
        'type':u'格式',
        'content': u'内容',
        'pic_url':u'图片地址',
        'enabled':u'启动'
    }


    id = db.Column(db.Integer,primary_key=True)
    wechat_group_id = db.Column(db.Integer,db.ForeignKey('wechat_group.id'))
    type = db.Column(db.SMALLINT,comment='1:message,0:pic_content')
    content = db.Column(db.Text)
    pic_url = db.Column(db.Text)
    enabled = db.Column(db.SMALLINT,comment='1:功能启用,0:此功能暂停')


@bp.route('/')
def index():
    return redirect(url_for('admin.index'))


@bp.route('check_login/')
def check_login():
    return jsonify(isLoggedIn=check_isLoggedIn())

