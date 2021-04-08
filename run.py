from __future__ import absolute_import, unicode_literals

"""
Copyright (c) 2020 - DevsBranch
"""
from sys import exit
from flask import g
from config import config_dict
from app import get_config_mode
from app import create_app
from app.base.forms import SearchForm

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

app, _ = create_app(app_config)


@app.before_request
def before_request():
    """
    This function make the Search form global, accessible in any template without
    passing it in render_template().
    """
    g.search_form = SearchForm()


if __name__ == "__main__":
    app.run(debug=True)
