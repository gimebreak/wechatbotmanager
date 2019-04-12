from .model import user_datastore,admin,db,Role,User
from .view.view import MyModelView,UserModelView
from flask import Flask,url_for
from flask_admin import helpers as admin_helpers
from flask_babelex import Babel
from flask_security import Security
from .view import main




def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    admin.init_app(app)
    db.init_app(app)
    babel = Babel(app)
    security = Security(app, user_datastore)

    admin.add_view(MyModelView(Role, db.session, name='权限管理'))
    admin.add_view(UserModelView(User, db.session, name='用户管理'))

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )
    app.app_context().push()
    app.register_blueprint(main,url_prefix='/')

    return app