import os
from config import DevelopmentConfig
from app import create_app
from app.model import db,Role,user_datastore
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from flask_security.utils import hash_password


app = create_app(DevelopmentConfig)
manager = Manager(app)
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)

def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import string
    import random

    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        test_user = user_datastore.create_user(
            name='admin',
            email='admin',
            password=hash_password('admin'),
            roles = [super_user_role,user_role]
        )

        test_user = user_datastore.create_user(
            name='zhang',
            email='zhang',
            password=hash_password('123123'),
            roles = [user_role]
        )


        roles=[user_role, super_user_role]
        #
        # first_names = [
        #     'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
        #     'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
        #     'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        # ]
        # last_names = [
        #     'Brown', 'Smith', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
        #     'Roberts', 'Khan', 'Lewis', 'Jackson', 'Clarke', 'James', 'Phillips', 'Wilson',
        #     'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
        # ]
        #
        # for i in range(len(first_names)):
        #     tmp_email = first_names[i].lower() + "." + last_names[i].lower() + "@example.com"
        #     tmp_pass = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))
        #     user_datastore.create_user(
        #         first_name=first_names[i],
        #         last_name=last_names[i],
        #         email=tmp_email,
        #         password=encrypt_password(tmp_pass),
        #         roles=[user_role, ]
        #     )
        db.session.commit()
    return

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop



if __name__ =='__main__':

    # Build a sample db on the fly, if one does not exist yet.
    # app_dir = os.path.realpath(os.path.dirname(__file__))
    # print(app)
    # database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    # print(database_path)
    # print(os.path.exists(database_path))
    # if not os.path.exists(database_path):
    # build_sample_db()
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()
    # app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)
