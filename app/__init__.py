# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

from flask import Flask
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()

from api.endpoints.user import user_endpoint


def register_extensions(app):
    db.init_app(app)
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


def create_app(config):
    app = Flask(__name__, static_folder="base/static")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    app.register_blueprint(user_endpoint)
    configure_database(app)
    return app
