from flask_admin.contrib import sqla
from flask import abort,redirect,url_for,request,jsonify
from flask_security import current_user

from flask_admin.base import expose
from flask_admin import babel
from flask_admin import AdminIndexView
from ..itchat.wechat_reader import get_qrimg
from . import bp
from ..itchat.wechat_reader import check_isLoggedIn



class WeChatAdminView(AdminIndexView):

    def __init__(self,name=None, category=None,
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
        global thread
        QRimg = get_qrimg()
        img_element = '<img id="qrimg" alt="Base64 encoded image" style="text-align: center" src="data:image/png;base64,{}"/>'.format(QRimg)
        return self.render(self._template,qrimg=img_element)





class MyModelView(sqla.ModelView):

# 可用来自定义view逻辑
    # @expose('/')
    # def index_view(self):
    #     print('hello')
    #     return super(MyModelView,self).index_view()

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser') or current_user.has_role('user')
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


class UserModelView(MyModelView):
    # column_searchable_list=('first_name','last_name')
    column_list = ('id','name','email','roles')
    column_labels = {
        'id': u'序号',
        'name': u'用户名',
        'email': u'邮箱',
        'active': u'激活',
        'roles': u'角色'
    }

class WeChatGroupView(MyModelView):
    column_list = ('id', 'wechat_info_id.nickname', 'username', 'nickname')
    column_labels = {
        'id': u'序号',
        'wechat_info_id.nickname': u'用户名',
        'username': u'群名称',
        'nickname': u'昵称',
    }




@bp.route('/')
def index():
    return redirect(url_for('admin.index'))


@bp.route('/check_login')
def check_login():
    return jsonify(isLoggedIn=check_isLoggedIn())
