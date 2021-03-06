from .model import user_datastore,db,Role,User

from .view.view import *
from flask import url_for
from flask_admin import helpers as admin_helpers
from flask_admin import Admin
from flask_babelex import Babel
from flask_security import Security
from .view import bp
from .itchat.itchatmain import app
from .model.model import *

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
    #
    admin.add_view(SuperUserView(Role, db.session, name='权限管理',category='设置'))
    admin.add_view(UserModelView(User, db.session, name='用户管理',category='设置'))
    admin.add_view(WeChatGroupView(WechatGroup, db.session, name='微信群'))
    admin.add_view(WechatMsgView(WechatMessage,db.session,name='微信群消息'))
    admin.add_view(WechatUserView(WechatUser,db.session,name='微信群用户'))
    admin.add_view(WechatWelcomeInfoView(WelcomeInfo,db.session,name='入群欢迎设置'))
    admin.add_view(AutoReplyView(AutoReply,db.session,name='自动回复'))
    admin.add_view(FavorateMsgView(FavorateMessage, db.session, name='收藏'))
    admin.add_view(AdNotificationGroupView(AdvNotificationGroup, db.session, name='广告通知群',category='消息过滤设置'))
    admin.add_view(AdWhiteListView(AdvWhitelistUser, db.session, name='广告白名单用户',category='消息过滤设置'))
    admin.add_view(AdvBlackList(AdvBlacklist, db.session, name='广告关键词',category='消息过滤设置'))
    admin.add_view(KWNotificationGroupView(KeywordNotificationGroup, db.session, name='关键词通知群',category='消息过滤设置'))
    admin.add_view(KWWhiteListView(KeywordWhitelistUser, db.session, name='关键词白名单用户',category='消息过滤设置'))
    admin.add_view(KWBlackList(KeywordBlacklist, db.session, name='关键词黑名单',category='消息过滤设置'))
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




