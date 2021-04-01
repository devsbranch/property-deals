# -*- encoding: utf-8 -*-

import os
from decouple import config


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = config("SECRET_KEY", default="S#perS3crEt_007")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "{}://{}:{}@{}:{}/{}".format(
        config("DB_ENGINE", default="postgresql"),
        config("DB_USERNAME", default="postgres"),
        config("DB_PASS", default="pass"),
        config("DB_HOST", default="localhost"),
        config("DB_PORT", default=5432),
        config("DB_NAME", default="appseed-flask"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "This!isAnAPIofSomeSort"
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    JWT_ACCESS_TOKEN_EXPIRES = 43200
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = "{}://{}:{}@{}:{}/{}".format(
        config("DB_ENGINE", default="postgresql"),
        config("DB_USERNAME", default="appseed"),
        config("DB_PASS", default="pass"),
        config("DB_HOST", default="localhost"),
        config("DB_PORT", default=5432),
        config("DB_NAME", default="appseed-flask"),
    )


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {"Production": ProductionConfig, "Development": DebugConfig}


S3_BUCKET_CONFIG = dict(
    S3_BUCKET=os.environ.get("S3_BUCKET"),
    S3_KEY=os.environ.get("AWS_ACCESS_KEY_ID"),
    S3_SECRET=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    S3_URL="https://{}.s3.amazonaws.com".format(os.environ.get("S3_BUCKET")),
    PROP_ASSETS="media/property-images/",
    USER_ASSETS="media/user-profile-images/",
    TEMP_DIR="media/tmp/",
)
