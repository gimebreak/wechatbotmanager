from .model import  User,Role,db
from flask_security import SQLAlchemyUserDatastore

class SqlAlchemyUserQueryStore(SQLAlchemyUserDatastore):
    def get_user(self, identifier):
        result = super(SqlAlchemyUserQueryStore,self).get_user(identifier)
        return result

user_datastore = SqlAlchemyUserQueryStore(db, User, Role)





