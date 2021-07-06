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

connexion_app, celery = create_app(app_config)
Migrate(connexion_app.app, db)


@connexion_app.app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User}


if DEBUG:
    connexion_app.app.logger.info('DEBUG       = ' + str(DEBUG))
    connexion_app.app.logger.info('Environment = ' + get_config_mode)
    connexion_app.app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)


if __name__ == "__main__":
    connexion_app.run(debug=True)
