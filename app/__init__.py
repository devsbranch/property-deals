# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

from __future__ import absolute_import, unicode_literals
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from decouple import config as db_config
from app import celeryapp


db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()

# importing from base module __init__
from api.endpoints import user_endpoint
from api.endpoints import property_endpoint


def register_extensions(app):
    ma.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)


def register_blueprints(app):
    for module_name in ("base", "home"):
        module = import_module("app.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


from config import config_dict

DEBUG = db_config("DEBUG", default=True)
get_config_mode = "Debug" if DEBUG else "Production"
app_config = config_dict[get_config_mode.capitalize()]

celery_beat_schedule = {
    "call-every-10": {
        "task": "app.tasks.user_query",
        "schedule": 4,
        "args": (1,),
    }
}


def create_app():
    app = Flask(__name__, static_folder="base/static")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config["SQLALCHEMY_DATABASE_URI"] = db_config("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["beat_schedule"] = celery_beat_schedule
    app.config.from_object(app_config)
    db.init_app(app)
    register_extensions(app)
    register_blueprints(app)
    celery = celeryapp.make_celery(app)
    print(type(celery))
    celeryapp.celery = celery
    app.register_blueprint(user_endpoint)
    app.register_blueprint(property_endpoint)
    configure_database(app)
    return app

