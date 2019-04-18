from .model import user_datastore,db,Role,User

from .view.view import *
from flask import url_for
from flask_admin import helpers as admin_helpers
from flask_admin import Admin
from flask_babelex import Babel
from flask_security import Security
from .view import bp
from .itchat.wechat_reader import app
from .model.User import *

def create_app(config):
    app.config.from_object(config)
    db.init_app(app)
    babel = Babel(app)
    security = Security(app, user_datastore)
    app.register_blueprint(bp,url_prefix='/')
    print(security._state)
    admin = Admin(
        index_view=WeChatAdminView(),
        name='JiaJia微信群管理',
        base_template='my_master.html',
        template_mode='bootstrap3',
    )

    admin.add_view(SuperUserView(Role, db.session, name='权限管理',category='设置'))
    admin.add_view(UserModelView(User, db.session, name='用户管理',category='设置'))
    admin.add_view(WeChatGroupView(Wechat_group, db.session, name='微信群'))
    admin.add_view(WechatMsgView(Wechat_message,db.session,name='微信群消息'))
    admin.add_view(WechatUserView(Wechat_user,db.session,name='微信群用户'))
    admin.add_view(WechatWelcomeInfoView(Welcome_info,db.session,name='入群欢迎设置'))
    admin.init_app(app)

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )

    app.app_context().push()

    return app




