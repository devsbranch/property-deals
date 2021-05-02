# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import boto3
import redis
from flask import Flask
from celery import Celery
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from elasticsearch import Elasticsearch
from decouple import config as sys_config

db = SQLAlchemy()
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()
jwt = JWTManager()
redis_client = redis.StrictRedis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", sys_config("AWS_ACCESS_KEY_ID")),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", sys_config("AWS_SECRET_ACCESS_KEY")),
)


def init_celery(app):
    """
    Create and initialize celery app.
    """
    task_list = [
        "app.tasks",
    ]
    celery = Celery(app.import_name, include=task_list)
    celery.conf.update(app.config)
    celery.conf.update(
        broker_url=os.environ.get("REDIS_URL", sys_config("REDIS_URL")),
        result_backend=os.environ.get("REDIS_URL", sys_config("REDIS_URL")),
        timezone="UTC",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)


def register_blueprints(app):
    for module_name in ('base', 'home'):
        module = import_module('app.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']])
    app.celery = init_celery(app)
    app.app_context().push()
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app, app.celery
