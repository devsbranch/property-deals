import os
import secrets
import shutil
import json
from PIL import Image
from flask import current_app
from app import celery
from app.base.models import User, Property
from app.base.file_handler import property_image_handler


@celery.task()
def update_user_data(data, username):
    User.update_user(data, username)
    return "User Updated"


@celery.task()
def save_property_data(temp_folder, form_data):
    prop_images_dir, images_list = property_image_handler(temp_folder)
    img_list_to_json = json.dumps(images_list)
    prop_images = {"photos": img_list_to_json, "image_folder": prop_images_dir}
    form_data.update(prop_images)
    Property.add_property(form_data)
    return "Property Created"


@celery.task()
def update_property_data(data, prop_id):
    Property.update_property(data, prop_id)
    return "Property Updated"

