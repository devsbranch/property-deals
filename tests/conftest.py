import os

import pytest
from flask import g
from decouple import config
from config import config_dict
from app import create_app, db
from app.base.forms import SearchForm


get_config_mode = "Debug" if config("DEBUG", default=False, cast=bool) else "Production"
app_config = config_dict[get_config_mode.capitalize()]  # get app configuration


@pytest.fixture(scope="module")
def flask_app():
    app = create_app(app_config)[0]
    # Enable the TESTING flag to disable the error catching during request handling
    # so that you get better error reports when performing test requests against the application.
    app.config["TESTING"] = True

    # use a separate database for testing
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "TESTING_DB", config("TESTING_DB")
    )

    # Disable CSRF tokens in the Forms (only valid for testing purposes!)
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture(scope="module")
def test_client(flask_app):
    with flask_app.app_context():
        db.create_all()
        with flask_app.test_request_context(), flask_app.test_client() as client:
            g.search_form = SearchForm()
            yield client
        db.drop_all()
