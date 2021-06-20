# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import g
from flask_migrate import Migrate
from sys import exit
from decouple import config

from config import config_dict, IMAGE_UPLOAD_CONFIG
from app import create_app, db
from app.base.models import User
from app.base.forms import SearchForm

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:

    # Load the configuration using the default values 
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app, celery = create_app(app_config)
Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User}


@app.before_request
def before_request():
    """
    This function make the Search form and the global profile_image_dir(used in the navigation.html) GLOBAL,
    accessible in any template without passing it in render_template().
    """
    g.search_form = SearchForm()
    g.profile_image_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["USER_PROFILE_IMAGES"]


if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)


if __name__ == "__main__":
    app.run()
