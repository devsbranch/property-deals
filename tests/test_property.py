import copy
import json
import os
import time
import botocore
from flask import current_app, url_for, g
from flask_login import current_user
from decouple import config
from app import db, s3
from app.base.models import Property, User
from config import IMAGE_UPLOAD_CONFIG
from .conftest import test_user_data, property_listing_data, register_user, login_user, logout_user

PROPERTY_IMAGES_DIR = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["PROPERTY_LISTING_IMAGES"]
IMAGE_STORAGE_CONF = os.environ.get(
    "IMAGE_STORAGE_LOCATION", config("IMAGE_STORAGE_LOCATION")
)


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


def test_create_property(test_client):
    """
    WHEN the '/create-property' page is requested (GET) and (POST) with user already logged in,
    THEN check the response is valid, assert the user is denied permission to list a Property because the email is
    not verified, manually verify user email by setting the "is_verified" attribute to True, assert that "jpg, jpeg, png"
    are the only allowed image extensions and assert listing the Property is successful after verifying the user.
    """
    register_user(test_client)
    login_user(test_client, username=test_user_data["username"], password=test_user_data["password"])

    response = test_client.get("/create-property", follow_redirects=True)
    assert response.status_code == 200
    assert b"Unverified Email" in response.data
    assert b"you have not verified your email hence you can't perform this action." in response.data

    user = User.query.filter_by(email=test_user_data["email"]).first()
    # Verify User
    user.is_verified = True
    db.session.commit()

    response_2 = test_client.get("/create-property", follow_redirects=True)
    assert response_2.status_code == 200
    assert b"Property Name" and "Property Description" and b"Upload photos of your property" in response_2.data
    
    new_test_data = copy.copy(property_listing_data)
    new_test_data["photos"] = (open("./tests/imgs_for_testing_listings/img-3.gif", "rb"), "img-3.gif")

    # Test only jpg, jpeg and png extensions are allowed
    response_3 = test_client.post("/create-property", data=new_test_data, follow_redirects=True)
    assert response_3.status_code == 200
    assert b"Only Images are allowed e.g jpg, jpeg, png" in response_3.data

    # Test listing Property
    response_4 = test_client.post("/create-property", data=property_listing_data, follow_redirects=True)
    assert response_4.status_code == 200
    assert b"Your Property has been listed." in response_4.data

    listed_property = Property.query.filter_by(name=property_listing_data["name"]).first()
    images_list = json.loads(listed_property.photos)  # e.g ["5de13ba062fa4/", "79cff318.jpg", "34cff3470.jpg"]

    # make a small delay compensate for the Celery task that handles images to complete then check
    # if the image exists
    time.sleep(4)

    # assert the image files for the property listing have been saved to the apps file system if the image storage 
    # configuration is set to "app_server_storage" else check the image files in the Amazon S3 bucket if 
    # the configuration is amazon_s3.
    assert (
        images_list[1]
        in os.listdir(f"{current_app.root_path}/base/static/{PROPERTY_IMAGES_DIR}{listed_property.images_folder}")
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else check_object_exist_on_s3(
            f"{PROPERTY_IMAGES_DIR}{listed_property.images_folder}{images_list[1]}"
        )
    )


def test_update_property(test_client):
    """
    WHEN the '/property/update/<id>' page is requested (GET) and (POST) with user already logged in,
    THEN check the response is valid, assert the user is denied permission to list a Property because the email is
    not verified, manually verify user email by setting the "is_verified" attribute to True, assert that "jpg, jpeg, png"
    are the only allowed image extensions, assert that the only the user who listed the Property can update it and
    assert that the listing of the Property is successful after verifying the user.
    """
    property_to_update = Property.query.filter_by(name=property_listing_data["name"]).first()

    # Un-verify user to test the @email_verification_required decorator is working as expected
    current_user.is_verified = False
    db.session.commit()

    response = test_client.get(f"/property/update/{property_to_update.id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Unverified Email" in response.data
    assert b"you have not verified your email hence you can't perform this action." in response.data

    # Verify User to be able to list a Property
    current_user.is_verified = True
    db.session.commit()

    # Test http error 404 is returned in the property id does not exist
    response_2 = test_client.get("/property/update/3984883", follow_redirects=True)
    assert response_2.status_code == 404

    response_3 = test_client.get(f"/property/update/{property_to_update.id}", follow_redirects=True)
    assert b"Property Name" and "Property Description" and b"Upload photos of your property" in response_3.data

    new_test_data = copy.copy(property_listing_data)
    new_test_data["photos"] = (open("./tests/imgs_for_testing_listings/img-3.gif", "rb"), "img-3.gif")

    response_4 = test_client.post(f"/property/update/{property_to_update.id}", data=new_test_data, follow_redirects=True)
    assert response_4.status_code == 200
    assert b"Only Images are allowed e.g jpg, jpeg, png" in response_4.data

    update_data = copy.copy(property_listing_data)
    update_data["name"] = "Apartment listing updated"
    update_data["desc"] = "A brief description updated"
    # Remove image file. Not needed here
    update_data.pop("photos")

    response_5 = test_client.post(
        f"/property/update/{property_to_update.id}",
        data=update_data,
        follow_redirects=True
    )
    assert response_5.status_code == 200
    assert b"Your Property listing has been updated" in response_5.data

    # Test update of Property listing images
    updated_property = Property.query.filter_by(name=update_data["name"]).first()
    assert updated_property is not None  # if True it means the name and description of the property was updated

    images_list = json.loads(updated_property.photos)  # e.g ["5de13ba062fa4/", "79cff318.jpg", "34cff3470.jpg"]

    # make a small delay compensate for the Celery task that handles images to complete then check
    # if the image exists
    time.sleep(4)

    # assert the image files for the property listing have been saved to the apps file system if the image storage
    # configuration is set to "app_server_storage" else check the image files in the Amazon S3 bucket if
    # the configuration is amazon_s3.
    assert (
        images_list[1]
        in os.listdir(f"{current_app.root_path}/base/static/{PROPERTY_IMAGES_DIR}{updated_property.images_folder}")
        if IMAGE_STORAGE_CONF == "app_server_storage"
        else check_object_exist_on_s3(
            f"{PROPERTY_IMAGES_DIR}{updated_property.images_folder}{images_list[1]}"
        )
    )

    # Revert to original attributes
    updated_property.name = property_listing_data["name"]
    updated_property.desc = property_listing_data["desc"]
    db.session.commit()


def test_property_details(test_client):
    """
    WHEN the '/details' page is requested (GET) with user already logged in,
    THEN check the response is valid, assert that the "Update" and "Delete" buttons are available if the logged in user
    is the one who created that listing and assert that the "Update" and "Delete" are not available if logged out.
    """
    listed_property = Property.query.filter_by(name=property_listing_data["name"]).first()
    assert listed_property is not None

    response = test_client.get(f"/property/details/{listed_property.id}")
    assert response.status_code == 200
    assert b"Update" and b"Delete Property?" in response.data

    # Test that accessing a listing with an id that doesn't exists returns a http 404 not found error
    response_2 = test_client.get("/property/details/3550")
    assert response_2.status_code == 404

    logout_user(test_client)
    response_3 = test_client.get(f"/property/details/{listed_property.id}")
    assert b"Update" and b"Delete Property?" not in response_3.data


def test_search_listing(test_client):
    """
    WHEN the '/delete-listing/<id>' page is requested (GET),
    THEN assert the response is 200 and assert the response the expected results depending on the search query passed
    to the url.
    """
    g.search_form.q.data = property_listing_data["name"]
    response = test_client.get(url_for("home_blueprint.search", q=g.search_form.q.data))
    assert response.status_code == 200
    assert b"Affordable Apartments on rent" and b"Apartments for rent at an affordable price." in response.data


def test_deleting_property(test_client):
    """
    WHEN the '/delete-listing/<id>' page is requested (GET),
    THEN assert the response is http error 403 if the user is not logged in, assert the response is http error 404 if
    a listing of an id provided doesn't exist, assert that only the user who listed that Property can delete it then
    assert that the deletion was successful
    """
    # Test user can't delete listing without login
    listed_property = Property.query.filter_by(name=property_listing_data["name"]).first()
    response = test_client.get(f"/delete-listing/{listed_property.id}")
    assert response.status_code == 403

    # Test that a http error 404 is returned if the id does not exist
    login_user(test_client, username=test_user_data["username"], password=test_user_data["password"])
    response_2 = test_client.get("/delete-listing/6875")
    assert response_2.status_code == 404

    # Test if the deletion was successful
    response_3 = test_client.get(f"/delete-listing/{listed_property.id}", follow_redirects=True)
    assert response_3.status_code == 200
    assert b"Your Property listing has been deleted" in response_3.data

    # Test the deleted listing is not in the database
    deleted = Property.query.filter_by(name=property_listing_data["name"]).first()
    assert deleted is None
