from flask_admin.contrib import sqla
from flask import abort,redirect,url_for,request,jsonify,current_app,render_template
from flask_security import current_user
from flask_admin.base import expose
from flask_admin import babel
from flask_admin import AdminIndexView
from . import bp
from copy import deepcopy
from ..model.model import *
from ..itchat.itchatmain import app
from  ..itchat.base import logger
from app.itchat.cron import last_week,last_month,the_week

from app.itchat.itchatmain import process


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
            return self.render(self._template)
        # 管理员权限可义读取图片登陆微信
        if current_user.is_authenticated and current_user.has_role('superuser'):
            logger.info('current user:{}'.format(current_user.name))

            try:
                id = current_user.get_id()
            except:
                logger.info('get current_user.id fialed')
                return self.render(self._template)
            # cur_user=deepcopy(current_user)
            # QRimg = get_qrimg(cur_user,app)
            QRimg = process(deepcopy(current_user))
            if QRimg:
                logger.info('success download QR info')
            if QRimg == None:
                return self.render(self._template)
            img_element = '<img id="qrimg" alt="Base64 encoded image" src="data:image/png;base64,{}"/>'.format(QRimg)

            return self.render(self._template,qrimg=img_element)
        else:
            return self.render(self._template)


class BaseView(sqla.ModelView):

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


class BaseUserView(sqla.ModelView):

# 可用来自定义view逻辑
    # @expose('/')
    # def index_view(self):
    #     print('hello')
    #     return super(MyModelView,self).index_view()

    def after_model_change(self, form, model, is_created):
        logger.info('开始更新名单')
        wechat_init=getattr(process,'wechat_init',None)
        if wechat_init ==None:
            logger.info('用户未登陆，无法获得wechat信息')
            return
        ad_notifs, ad_uncensor, ad_keywords = wechat_init.load_adv_rule()
        process.rule ={'ad_rule':[],'keyword_rule':[]} #清零
        process.rule['ad_rule'].extend([ad_notifs, ad_uncensor, ad_keywords])
        k_notifs, k_uncensor, k_keyword = wechat_init.load_keyword_rule()
        process.rule['keyword_rule'].extend([k_notifs, k_uncensor, k_keyword])

        logger.info("更新了广告过滤信息，广告过滤通知群:{},广告过滤白名单{},"
                    "广告过滤关键字{}".format(str(ad_notifs), str(ad_uncensor), str(ad_keywords)))
        logger.info( "更新了关键字信息，关键字通知群:{},关键字白名单{},"
                     "关键字{}".format(str(k_notifs), str(k_uncensor), str(k_keyword)))



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


    # 用户只能查看数据库中自己的微信信息
    # def get_list(self, page, sort_column, sort_desc, search, filters,
    #              execute=True, page_size=None):
    #     # print(filters)
    #     # print('this is filter')
    #     #
    #     # for i in current_user.infos:
    #     #     filters.append((5, 'Wechat User Id', str(i.id)))
    #     # print(filter)
    #     count,query = super(BaseUserView,self).get_list(page, sort_column, sort_desc, search, filters,
    #              execute=False, page_size=None)
    #     # 当前用户的infos
    #     user_record = User.query.get(current_user.get_id()).infos
    #     res = []
    #     # 当前model 过滤条件为用户info
    #
    #     for info in user_record:
    #         res += query.from_self().filter_by(wechat_info_id=info.id).all()
    #     query = res
    #
    #     return count,query


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
            group_records += WechatGroup.query.filter_by(wechat_info_id=info.id).all()

        for group in group_records:
            res += query.from_self().filter_by(wechat_group_id=group.id).all()
        query = res

        return count,query

class SuperUserView(sqla.ModelView):

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
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
    column_list = ('id','info','nickname','membercount')
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

    form_ajax_refs = {
        'users': {
            'fields': ('id', 'nickname'),
            'page_size': 10
        }
    }
    #内联模型: 只有one2many才可进行内联编辑
    # inline_models = (Wechat_user,)
    # form_columns = (Wechat_group.id,Wechat_group.users)

class WechatMsgView(SuperUserView):
    column_list = ('id','wechat_user','group.nickname','message','createtime','favorate')
    column_labels = {
        'id':u'序号',
        'wechat_user':u'微信名',
        'wechat_user.nickname':'微信名',
        'group.nickname': '所在群',
        'message':'消息内容',
        'createtime':'创建时间',
        'favorate':'收藏',
        'info':'归属用户'
    }
    column_sortable_list =('createtime','favorate','wechat_user.group.nickname')
    column_filters = ('group.nickname','wechat_user.nickname')
    column_editable_list=('favorate',)
    column_default_sort = ('createtime', True)

class WechatUserView(SuperUserView):
    column_list = ('id', 'nickname','group.nickname','parent' )
    column_labels = {
        'id': u'序号',
        'nickname': u'微信名',
        'group.nickname':u'所属群',
        'parent':'邀请人'
    }
    column_filters = ('group.nickname',)


class WechatWelcomeInfoView(GroupBasedView):

    def after_model_change(self, form, model, is_created):
        wechat_init = getattr(process, 'wechat_init', None)
        logger.info("开始更新自动欢迎通知列表{}")
        if wechat_init == None:
            logger.info('用户未登陆，无法获得wechat信息')
        process.welcome_list = wechat_init.load_welcomeinfo()
        logger.info("更新了自动欢迎通知列表{}".format(str(process.welcome_list)))



    column_list = ('id', 'group','type','content','pic_url','enabled' )
    column_labels = {
        'id': u'序号',
        'group':u'所属群',
        'type':u'格式',
        'content': u'内容',
        'pic_url':u'图片地址',
        'enabled':u'启动'
    }

class FavorateMsgView(BaseUserView):
    column_list = ('id','message')
    column_labels = {
        'id':u'序号',
        'message':u'消息'
    }

class AdNotificationGroupView(BaseUserView):
    column_list = ('id','group')
    column_labels = {
        'id':u'序号',
        'group':u'通知群'
    }

class AdWhiteListView(BaseUserView):
    column_list = ('id','wechat_user')
    column_labels = {
        'id':u'序号',
        'wechat_user':'微信用户'
    }

class AdvBlackList(BaseUserView):
    column_list = ('id','keyword')
    column_labels = {
        'id':u'序号',
        'keyword':'关键字'
    }


class KWNotificationGroupView(BaseUserView):
    column_list = ('id', 'group')
    column_labels = {
        'id': u'序号',
        'group': u'通知群'
    }


class KWWhiteListView(BaseUserView):
    column_list = ('id','wechat_user')
    column_labels = {
        'id': u'序号',
        'wechat_user': '微信用户'
    }


class KWBlackList(BaseUserView):
    column_list = ('id', 'keyword')
    column_labels = {
        'id': u'序号',
        'keyword': '关键字'
    }

class AutoReplyView(SuperUserView):
    column_list = ('id','type','group','keyword','reply_content','enabled')
    column_labels = {
        'id': u'序号',
        'type':u'发送方式',
        'keyword': '关键字',
        'group':'群名称',
        'reply_content':'回复内容',
        'enabled':'是否启动'
    }

    def after_model_change(self, form, model, is_created):
        wechat_init = getattr(process, 'wechat_init', None)
        logger.info('开始更新自动回复列表')
        if wechat_init == None:
            logger.info('用户未登陆，无法获得wechat信息')
            return

        process.auto_replies = wechat_init.load_auto_reply()
        logger.info("更新了自动回复列表{}".format(str(process.auto_replies)))

from flask_admin.base import BaseView


class TheWeekView(BaseView):

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
        )

    #本周
    @expose()
    def the_week(self):
        start,end = the_week()
        groups = WechatGroup.query.filter_by().all()
        msg_num_dict = {}
        for g in groups:
            msg_count = 0
            users = g.users
            for u in users:
                msgs = u.msgs
                for m in msgs:
                    createtime = m.createtime
                    if(createtime>start and createtime<end):
                        msg_count+=1
            msg_num_dict.update({g.nickname:[msg_count,g.id]})
        render_args= sorted(msg_num_dict.items(),key=lambda x:x[1][0],reverse=True)
        # print(render_args)
        return self.render('ranklist_master.html',ranklist=render_args,type="theweek")


class LastWeekView(BaseView):

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
        )

    #本周
    @expose()
    def last_week(self):
        start,end = last_week()
        groups = WechatGroup.query.filter_by().all()
        msg_num_dict = {}
        for g in groups:
            msg_count = 0
            users = g.users
            for u in users:
                msgs = u.msgs
                for m in msgs:
                    createtime = m.createtime
                    if(createtime>start and createtime<end):
                        msg_count+=1
            msg_num_dict.update({g.nickname:[msg_count,g.id]})
        render_args= sorted(msg_num_dict.items(),key=lambda x:x[1][0],reverse=True)
        # print(render_args)
        return self.render('ranklist_master.html',ranklist=render_args,type="lastweek")

class LastMonthView(BaseView):


    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
        )
    #本周
    @expose()
    def last_month(self):
        start,end = last_month()
        groups = WechatGroup.query.filter_by().all()
        msg_num_dict = {}
        for g in groups:
            msg_count = 0
            users = g.users
            for u in users:
                msgs = u.msgs
                for m in msgs:
                    createtime = m.createtime
                    if(createtime>start and createtime<end):
                        msg_count+=1
            msg_num_dict.update({g.nickname:[msg_count,g.id]})
        render_args= sorted(msg_num_dict.items(),key=lambda x:x[1][0],reverse=True)
        # print(render_args)
        return self.render('ranklist_master.html',ranklist=render_args,type="lastmonth")



class UserMessageView(BaseView):
    '''
    type:lastweek,week,month
    id: group_id
    '''

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('user')
        )

    @expose()
    def user_message(self):
        #
        group_id = request.args.get('id')
        type = request.args.get('type')
        if type== "theweek":
            start,end = the_week()
        elif type== "lastweek":
            start,end = last_week()
        elif type == "lastmonth":
            start,end =last_month()
        else:start,end = 0,0
        group = WechatGroup.query.get(group_id)
        users = group.users
        msg_num_dict = {}
        for u in users:
            msg_count = 0
            msgs = u.msgs
            for m in msgs:
                createtime = m.createtime
                if(createtime>start and createtime<end):
                    msg_count+=1
            msg_num_dict.update({u.nickname:msg_count})
        render_args= sorted(msg_num_dict.items(),key=lambda x:x[1],reverse=True)
        return self.render('user_ranklist_matser.html',args = render_args)



@bp.route('/')
def index():
    return redirect(url_for('admin.index'))


@bp.route('check_login/')
def check_login():
    return jsonify(isLoggedIn=process.isLoggedIn)


from flask_login.signals import user_logged_in
@user_logged_in.connect_via(app)
def user_loggin(sender,user):
    #可以直接操作app上下文
    print(WechatMessage.query.get(1))