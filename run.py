from __future__ import absolute_import, unicode_literals

"""
Copyright (c) 2020 - DevsBranch
"""
from sys import exit
from config import config_dict
from app import get_config_mode
from app import create_app

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

app, _ = create_app(app_config)

if __name__ == "__main__":
    app.run(debug=True)
