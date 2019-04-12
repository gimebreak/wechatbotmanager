from flask_admin.contrib import sqla
from flask import abort,redirect,url_for,request
from flask_security import current_user
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from app.model import User

class MyModelView(sqla.ModelView):
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

from . import main
@main.route('/')
def index():
    return redirect(url_for('admin.index'))