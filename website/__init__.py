from os import path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_apscheduler import APScheduler


database = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()
login_manager = LoginManager()
DATABASE_NAME = "VDMDatabase.db"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "MYSECRETKEY567"
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{path.join('/database',DATABASE_NAME)}"  
    )"""  # To run this locally change to
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_NAME}"
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587  # TLS PORT FOR GMAIL
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "devicemanagementprojecttest@gmail.com"
    app.config["MAIL_PASSWORD"] = "QaDummyPassword1"
    app.config["MAIL_DEFAULT_SENDER"] = "devicemanagementprojecttest@gmail.com"
    app.config["SCHEDULER_API_ENABLED"] = True
    scheduler.init_app(app)
    scheduler.start()
    mail.init_app(app)

    database.init_app(app)
    """
    fix emails and scheldues
    fix init py 
    pytest
    lint everything
    try and bypass git commit
    """
    from .models import User
    from .views import views_blueprint
    from .authentication_page_routing import authentication_blueprint
    from .reservation_page_routing import reservation_blueprint
    from .device_page_routing import device_blueprint
    from .user_page_routing import user_blueprint

    app.register_blueprint(views_blueprint, url_prefix="/")
    app.register_blueprint(authentication_blueprint, url_prefix="/")
    app.register_blueprint(device_blueprint, url_prefix="/device")
    app.register_blueprint(reservation_blueprint, url_prefix="/reservation")
    app.register_blueprint(user_blueprint, url_prefix="/user")

    create_database(app)

    login_manager.login_view = "authentication.login_page"
    login_manager.init_app(app)

    # Links login_manager user to the User database
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    return app


def create_database(app):

    if not path.exists("QaProjectAgile/" + DATABASE_NAME):
        with app.app_context():
            database.create_all()
        print("Created Database!")
