from flask import Flask
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config, TestingConfig
import sqlalchemy as sa
import sqlalchemy.orm as so


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'routes.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)


    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='GidGud Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/gidgud.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('GidGud startup')

    if app.debug and not app.testing:

        if not os.path.exists('logs'):
            os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/gidgud.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            # sql logging
            #logging.basicConfig()
            #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
            #logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())
            # end

            app.logger.setLevel(logging.INFO)
            app.logger.info('GidGud startup')

        else:
            file_handler = RotatingFileHandler('logs/gidgud.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            # sql logging
            #logging.basicConfig()
            #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
            #logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())
            # end

            app.logger.setLevel(logging.INFO)
            app.logger.info('GidGud startup')

    if app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/gidgud.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('GidGud Test startup')

    @app.shell_context_processor
    def make_shell_context():
        return {'sa': sa, 'so': so, 'db': db}

    return app
