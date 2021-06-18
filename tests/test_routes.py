import time
import os
import botocore
from decouple import config
from flask import current_app
from werkzeug.security import check_password_hash
from app import s3
from app.base.models import User
from config import IMAGE_UPLOAD_CONFIG


PROFILE_IMAGE_DIR = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["USER_PROFILE_IMAGES"]
COVER_IMAGE_DIR = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["USER_COVER_IMAGES"]
IMAGE_STORAGE_CONF = os.environ.get(
    "IMAGE_STORAGE_LOCATION", config("IMAGE_STORAGE_LOCATION")
)

test_user_data = dict(
    first_name="John",
    last_name="Doe",
    gender="Male",
    phone="123456789",
    username="johndoe",
    email="johndoe@mail.com",
    password="pass1234",
)

test_user_data_2 = dict(
    first_name="Jane",
    last_name="Doe",
    gender="Male",
    phone="123456789",
    username="janedoe",
    email="janedoe@mail.com",
    password="pass1234",
)


def login(test_client, username, password):
    return test_client.post(
        "/login", data=dict(username=username, password=password), follow_redirects=True
    )


def logout(test_client):
    return test_client.get("/logout", follow_redirects=True)


def check_object_exist_on_s3(obj_path):
    """
    This function checks if an object exists on Amazon S3 specifically an image. It is useful
    for testing if the image upload was successful to s3 when posting data to the "/my-profile",
    "/create-property" and "/update-property".
    """
    bucket = os.environ.get("S3_BUCKET", config("S3_BUCKET"))
    try:
        time.sleep(
            4
        )  # make a small delay compensate for the Celery task that handles images to complete then check if
        # the object exists
        s3.head_object(Bucket=bucket, Key=obj_path)
        return True
    except botocore.client.ClientError:
        return False


def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

    # "Create Property" and "My Listings" are only available if user has logged in.
    assert b"Create Property" and b"My Listings" not in response.data


def test_registration(test_client):
    """
    Test if the registration functionality works.
    GIVEN a Flask application
    WHEN the '/register' page is requested (POST)
    THEN check the response is valid, check that the flash message ("Your account has been created. Check your inbox to
    verify your email.") attribute is present in the html. We also test that the registered user is in the database and
    the password is hashed.
    """
    response = test_client.post("/register", data=test_user_data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Sign in" in response.data
    assert (
        b"Your account has been created. Check your inbox to verify your email."
        in response.data
    )
    registered_user = User.query.filter_by(email=test_user_data["email"]).first()
    assert registered_user is not None
    assert registered_user.username == test_user_data["username"]
    assert registered_user.email == test_user_data["email"]
    assert registered_user.password != test_user_data["password"]
    assert (
        check_password_hash(registered_user.password, test_user_data["password"])
        is True
    )


def test_login(test_client):
    """
    GIVEN a Flask application
    WHEN the '/login' page is requested (POST)
    THEN check the response is valid, check that the attributes in the html available to a logged in user are present
    """
    response = login(
        test_client,
        username=test_user_data["username"],
        password=test_user_data["password"],
    )
    assert response.status_code == 200

    # The attributes below should be available in the html if the user has logged in
    assert b"Create Property" and b"My Listings" in response.data
    assert b"My Profile" and b"Logout" in response.data


def test_user_unverified_email(test_client):
    """
    GIVEN a Flask application
    WHEN the '/create-property' page is requested (GET)
    THEN check the response is valid, check that the flash message ("You need to verify your email first") is in the
    response data.
    """
    response = test_client.get("/create-property", follow_redirects=True)
    assert response.status_code == 200
    assert (
        b"Unverified Email"
        and b"You need to verify your email first"
        and b"Resend" in response.data
    )


def test_user_profile_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/my-profile' page is requested (GET)
    THEN check the response is valid and that response.data has the expected data.
    """
    response = test_client.get("/my-profile")
    assert response.status_code == 200
    assert (
        b"Sign Out"
        and b"Select profile photo"
        and b"Select cover photo" in response.data
    )

    # Test updating of first name and last_name
    response_2 = test_client.post(
        "/my-profile",
        data=dict(first_name="test_user_updated", last_name="test_user_lastname"),
        follow_redirects=True,
    )
    updated_user = User.query.filter_by(email=test_user_data["email"]).first()

    assert response.status_code == 200
    assert b"Your account information has been updated." in response_2.data
    assert (
        updated_user.first_name == "test_user_updated"
        and updated_user.last_name == "test_user_lastname"
    )


def test_user_profile_photo_uploads(test_client):
    """
    GIVEN a Flask application
    WHEN the '/my-profile' page is requested (POST) with images included
    THEN check the response is valid, that response.data has the expected data, and that the images are processed
    and saved to the app server or Amazon S3 depending on the configurations.
    """
    # open image files to be submitted, since the data should be sent as binary(bytes stream).
    test_user_data["profile_photo"] = (
        open("./tests/imgs_for_testing_user_profile/default.jpg", "rb"),
        "default.jpg",
    )
    test_user_data["cover_photo"] = (
        open("./tests/imgs_for_testing_user_profile/default_cover.jpg", "rb"),
        "default_cover.jpg",
    )

    response = test_client.post(
        "/my-profile", data=test_user_data, follow_redirects=True
    )

    updated_user = User.query.filter_by(email=test_user_data["email"]).first()
    assert response.status_code == 200
    assert b"Your account information has been updated." in response.data

    assert (
        updated_user.prof_photo_loc == "app_server_storage"
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else (updated_user.prof_photo_loc == "amazon_s3")
    )

    assert (
        updated_user.cover_photo_loc == "app_server_storage"
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else updated_user.cover_photo_loc == "amazon_s3"
    )
    # assert if the profile image saved to the app server or Amazon S3 depending on the configurations.
    assert (
        updated_user.profile_photo
        in os.listdir(f"{current_app.root_path}/base/static/{PROFILE_IMAGE_DIR}")
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else check_object_exist_on_s3(
            f"{PROFILE_IMAGE_DIR}{updated_user.profile_photo}"
        )
        is True
    )

    # assert if the cover image saved to the app server or Amazon S3 depending on the configurations.
    assert (
        updated_user.cover_photo
        in os.listdir(f"{current_app.root_path}/base/static/{COVER_IMAGE_DIR}")
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else check_object_exist_on_s3(f"{COVER_IMAGE_DIR}{updated_user.cover_photo}")
        is True
    )


def test_username_email_exist_err(test_client):
    """
    GIVEN a Flask application
    WHEN the '/my-profile' page is requested (POST) with images included
    THEN check the response is valid, that response.data has the expected data, in this case, the flash messages
    ""The username is already taken. Please try a different one." and "The email you entered is already registered.
    Please try a different one." should be in response.data.
    """

    # Here we register a another user (Jane Doe) and use the same data Jane Doe to update the profile of the
    # current/logged in user (John Doe). See the assertions below.
    test_client.post("/register", data=test_user_data_2, follow_redirects=True)

    # Updating the profile of John Doe with the data of Jane Doe. See the assertions below.
    response = test_client.post("/my-profile", data=test_user_data_2, follow_redirects=True)

    assert response.status_code == 200
    assert b"The email you entered is already registered. Please try a different one." in response.data
    assert b"The username is already taken. Please try a different one." in response.data
