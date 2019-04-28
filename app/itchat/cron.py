from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from ..model.model import *
from .itchatmain import app
from .tool import logger


def the_week():
    current_time = datetime.today()
    current_day = datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0)
    day = timedelta(current_time.weekday())
    monday = current_day-day
    return monday,datetime.now()


def last_week():
    current_time = datetime.today()
    current_day = datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0)
    day = timedelta(current_time.weekday())
    monday = current_day-day
    return monday-timedelta(7),monday

def last_month():
    current_time = datetime.today()
    the_month = datetime(current_time.year, current_time.month, 1, 0, 0, 0)
    one_month_delta = relativedelta(months=1)
    last_month = the_month - one_month_delta
    return last_month,the_month

def update_activation():
    week_msg = get_week_activation()
    month_msg = get_month_activation()
    with app.app_context():
        for name,wnum in week_msg.items():
            mnum = month_msg[name]['count']
            group_id =month_msg[name]['id']
            ga = GroupActivation(week_activation=wnum['count'],month_activation=mnum,
                                 wechat_group_id=group_id,createtime=datetime.now())
            db.session.add(ga)
            print(ga)
            print(ga.week_activation,ga.month_activation)
        try:
            db.session.commit()
            logger.info('活跃度计算写入成功')
        except:
            logger.error('活跃度计算写入失败')


def get_week_activation():
    start,end = the_week()
    with app.app_context():
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
            msg_num_dict.update({g.nickname: {'count':msg_count,'id':g.id}})
        print(msg_num_dict)

        return msg_num_dict

def get_month_activation():
    start, end = last_month()
    with app.app_context():
        groups = WechatGroup.query.filter_by().all()
        msg_num_dict = {}
        for g in groups:
            msg_count = 0
            users = g.users
            for u in users:
                msgs = u.msgs
                for m in msgs:
                    createtime = m.createtime
                    if (createtime > start and createtime < end):
                        msg_count += 1

            msg_num_dict.update({g.nickname: {'count':msg_count,'id':g.id}})
        print(msg_num_dict)
        return msg_num_dict