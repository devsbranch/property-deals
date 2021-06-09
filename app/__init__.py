# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import boto3
import redis
from pathlib import Path
from flask import Flask, current_app
from celery import Celery
from celery.schedules import crontab
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from elasticsearch import Elasticsearch
from decouple import config as sys_config
from config import IMAGE_UPLOAD_CONFIG
from dotenv import load_dotenv
from app.search import PropertyDataMapping

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()
jwt = JWTManager()
redis_client = redis.StrictRedis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379")
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get(
        "AWS_ACCESS_KEY_ID", sys_config("AWS_ACCESS_KEY_ID")
    ),
    aws_secret_access_key=os.environ.get(
        "AWS_SECRET_ACCESS_KEY", sys_config("AWS_SECRET_ACCESS_KEY")
    ),
)


def init_celery(flask_app):
    """
    Create and initialize celery app.
    """
    from app.base.models import DeactivatedUserAccounts

    # Serialize the data from the DeactivatedUserAccounts table into a python dictionary so that Celery can
    # serialize the data to JSON

    class AccountDataSchema(ma.Schema):
        class Meta:
            # Fields to expose
            fields = ("id", "email", "username")

    accounts_data_schema = AccountDataSchema(many=True)
    with flask_app.app_context():
        queried_data = DeactivatedUserAccounts.query.all()

    task_list = [
        "app.tasks",
    ]
    celery = Celery(flask_app.import_name, include=task_list)
    celery.conf.update(flask_app.config)
    celery.conf.update(
        broker_url=os.environ.get("REDIS_URL", sys_config("REDIS_URL")),
        timezone="UTC",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        beat_schedule={
            "delete_user_account": {
                "task": "app.tasks.delete_user_account",
                "schedule": crontab(),
                "args": (accounts_data_schema.dump(queried_data),),
            }
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
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
    for module_name in ("base", "home"):
        module = import_module("app.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database_and_index_data():
        db.create_all()
        PropertyDataMapping.init()  # Create the index and mappings in ElasticSearch

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_image_upload_directories():
    """
    Create directories at application runtime.
    """
    paths = {
        "profile_image_upload_dir": IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
            "USER_PROFILE_IMAGES"
        ],
        "cover_image_upload_dir": IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
            "USER_COVER_IMAGES"
        ],
        "temp_image_dir": IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["TEMP_DIR"],
        "property_listing_images_dir": IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
            "PROPERTY_LISTING_IMAGES"
        ],
    }
    for path in paths.keys():
        path_name = Path(f"{current_app.root_path}/base/static/{paths[path]}")
        path_name.mkdir(parents=True, exist_ok=True)


def create_app(config):
    app = Flask(__name__, static_folder="base/static")
    app.config.from_object(config)
    register_extensions(app)
    app.elasticsearch = Elasticsearch([app.config["ELASTICSEARCH_URL"]])
    app.celery = init_celery(app)
    app.app_context().push()
    register_blueprints(app)
    configure_database(app)
    create_image_upload_directories()
    return app, app.celery
