# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import config


class Config(object):
    # Set up the App SECRET_KEY
    SECRET_KEY = os.environ.get("SECRET_KEY", config("SECRET_KEY"))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "{}://{}:{}@{}:{}/{}".format(
            config("DB_ENGINE", default="postgresql"),
            config("DB_USERNAME", default="postgres"),
            config("DB_PASS", default="pass"),
            config("DB_HOST", default="localhost"),
            config("DB_PORT", default=5432),
            config("DB_NAME", default="flask_app_db"),
        ))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", config("JWT_SECRET_KEY"))
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    JWT_ACCESS_TOKEN_EXPIRES = 43200
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
    RESULTS_PER_PAGE = 25


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE', default='postgresql'),
        config('DB_USERNAME', default='appseed'),
        config('DB_PASS', default='pass'),
        config('DB_HOST', default='localhost'),
        config('DB_PORT', default=5432),
        config('DB_NAME', default='appseed-flask')
    )


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}

IMAGE_UPLOAD_CONFIG = {
    "AMAZON_S3": {
        "S3_BUCKET": os.environ.get("S3_BUCKET", config("S3_BUCKET")),
        "S3_KEY": os.environ.get("AWS_ACCESS_KEY_ID", config("AWS_ACCESS_KEY_ID")),
        "S3_SECRET": os.environ.get("AWS_SECRET_ACCESS_KEY", config("AWS_SECRET_ACCESS_KEY")),
        "S3_URL": "https://{}.s3.amazonaws.com".format(os.environ.get("S3_BUCKET", config("S3_BUCKET"))),
    },
    "IMAGE_SAVE_DIRECTORIES": {
        "PROPERTY_LISTING_IMAGES": "assets/images/listings/",
        "USER_PROFILE_IMAGES": "assets/images/user/profile/",
        "USER_COVER_IMAGES": "assets/images/user/cover/",
        "TEMP_DIR": "assets/images/temp/"
    },
    "STORAGE_LOCATION": os.environ.get("IMAGE_STORAGE_LOCATION", config("IMAGE_STORAGE_LOCATION"))
}
