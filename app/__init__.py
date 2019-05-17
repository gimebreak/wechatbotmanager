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
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect


def create_app(config):
    app.config.from_object(config)
    db.init_app(app)
    babel = Babel(app)
    security = Security(app, user_datastore)
    app.register_blueprint(bp,url_prefix='/')
    admin = Admin(
        index_view=WeChatAdminView(),
        name='JiaJia微信群管理',
        base_template='my_master.html',
        template_mode='bootstrap3',
    )

    CSRFProtect(app)

    #
    admin.add_view(SuperUserView(Role, db.session, name='权限管理',category='设置'))
    admin.add_view(UserModelView(User, db.session, name='用户管理',category='设置'))
    admin.add_view(WeChatGroupView(WechatGroup, db.session, name='微信群'))
    admin.add_view(WechatMsgView(WechatMessage,db.session,name='微信群消息'))
    admin.add_view(WechatUserView(WechatUser,db.session,name='微信群用户'))
    admin.add_view(WechatWelcomeInfoView(WelcomeInfo,db.session,name='入群欢迎设置'))
    admin.add_view(AutoReplyView(AutoReply,db.session,name='自动回复'))
    # admin.add_view(FavorateMsgView(FavorateMessage, db.session, name='收藏'))
    admin.add_view(AdNotificationGroupView(AdvNotificationGroup, db.session, name='广告通知群',category='消息过滤设置'))
    admin.add_view(AdWhiteListView(AdvWhitelistUser, db.session, name='广告白名单用户',category='消息过滤设置'))
    admin.add_view(AdvBlackList(AdvBlacklist, db.session, name='广告关键词',category='消息过滤设置'))
    admin.add_view(KWNotificationGroupView(KeywordNotificationGroup, db.session, name='关键词通知群',category='消息过滤设置'))
    admin.add_view(KWWhiteListView(KeywordWhitelistUser, db.session, name='关键词白名单用户',category='消息过滤设置'))
    admin.add_view(KWBlackList(KeywordBlacklist, db.session, name='关键词黑名单',category='消息过滤设置'))
    admin.add_view(TheWeekView(name='本周热度', category='群热度排行'))
    admin.add_view(LastWeekView(name='上周热度',category='群热度排行'))
    admin.add_view(LastMonthView(name='上月热度', category='群热度排行'))
    admin.add_view(UserMessageView(name='用户明细(不可点)',category='群热度排行'))

    admin.init_app(app)

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()


    app.app_context().push()

    return app




