from flask_sqlalchemy import SQLAlchemy
from .User import  User,Role,db
import flask_admin
from flask_security import SQLAlchemyUserDatastore


user_datastore = SQLAlchemyUserDatastore(db, User, Role)

admin = flask_admin.Admin(
    name = 'Example: Auth',
    base_template='my_master.html',
    template_mode='bootstrap3',
)