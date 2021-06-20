import pytest
from decouple import config
from config import config_dict, Config
from app import create_app, db


get_config_mode = "Debug" if config("DEBUG", default=False, cast=bool) else "Production"
app_config = config_dict[get_config_mode.capitalize()]  # get app configuration


test_user_data = dict(
    first_name="John",
    last_name="Doe",
    gender="Male",
    phone="123456789",
    username="johndoe",
    email="johndoe0001234567@mail.com",
    password="pass1234",
)

test_user_data_2 = dict(
    first_name="Jane",
    last_name="Doe",
    gender="Male",
    phone="123456789",
    username="janedoe",
    email="janedoe0001234567@mail.com",
    password="pass1234",
)

property_listing_data = dict(
    name="Affordable Apartments on rent",
    desc="Apartments for rent at an affordable price.",
    type="Rent",
    photos=[
        (open("./tests/imgs_for_testing_listings/img-1.jpg", "rb"), "mg-1.jpg")
    ],
    price="Negotiable",
    location="my location"
)


def register_user(test_client):
    return test_client.post(
        "/register",
        data=test_user_data,
        follow_redirects=True
    )


def login_user(test_client, username, password):
    return test_client.post(
        "/login", data=dict(username=username, password=password), follow_redirects=True
    )


def logout_user(test_client):
    return test_client.get("/logout", follow_redirects=True)


@pytest.fixture(scope="module")
def flask_app():
    app = create_app(app_config)[0]
    # Enable the TESTING flag to disable the error catching during request handling
    # so that you get better error reports when performing test requests against the application.
    app.config["TESTING"] = True

    # use a separate database for testing
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI

    # Disable CSRF tokens in the Forms (only valid for testing purposes!)
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture(scope="module")
def test_client(flask_app):
    with flask_app.app_context():
        db.create_all()
        with flask_app.test_request_context(), flask_app.test_client() as client:
            yield client
        db.drop_all()
