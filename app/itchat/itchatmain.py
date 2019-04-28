import itchat
import base64
from .tool import Process_Wechat,WechatBaseData
from flask import Flask
from ..model import db
from datetime import datetime
import re,random
from time import sleep
from .base import BaseProcess
from itchat.content import *


app = Flask(__name__)

process = BaseProcess(app=app,itchat=itchat,db=db)




