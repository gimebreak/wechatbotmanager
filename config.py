from flask import config

class DevelopmentConfig(object):
    # Create dummy secrey key so we can use sessions
    SECRET_KEY = '123456790'

    # Create in-memory database
    # DATABASE_FILE = 'jiajiawechat?charset=utf8mb 4&autocommit=true'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/' + DATABASE_FILE
    DATABASE_FILE ='sample_db.sqlite'
    SQLALCHEMY_DATABASE_URI='sqlite:///'+DATABASE_FILE
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Flask-Security config
    SECURITY_URL_PREFIX = "/admin"
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_PASSWORD_SALT = "ATGUOHAELKiubahiughaerGOJAEGj"

    # Flask-Security URLs, overridden because they don't put a / at the end
    SECURITY_LOGIN_URL = "/login/"
    SECURITY_LOGOUT_URL = "/logout/"
    SECURITY_REGISTER_URL = "/register/"

    SECURITY_POST_LOGIN_VIEW = "/admin/"
    SECURITY_POST_LOGOUT_VIEW = "/admin/"
    SECURITY_POST_REGISTER_VIEW = "/admin/"

    # Flask-Security features
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False

    # internationalization
    BABEL_DEFAULT_LOCALE = 'zh_hans_CN'

    # flask-apscheduler

    # JOBS = [
    #     {
    #         'id': 'job1',
    #         'func': 'app.itchat.cron:update_activation',
    #         'trigger': {
    #             'type': 'cron',
    #             'day_of_week': "sun",
    #             'hour': '*',
    #             'minute': '*',
    #             'second': '*/30'
    #         }
    #     }
    # ]
    # SCHEDULER_API_ENABLED = True