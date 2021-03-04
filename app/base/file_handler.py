import os
import random
import string
import shutil
from PIL import Image
from werkzeug.utils import secure_filename
import secrets
from flask import current_app
from app import db


def create_images_folder(username):
    """
    Generates a random string which will be used as a folder name for storing image files
    of properties uploaded by user.
    """
    s = string.ascii_letters
    output_str = "".join(random.choice(s) for i in range(10))
    property_img_folder = f"property_images/{username}-property{output_str}"
    os.mkdir(f"{current_app.root_path}/base/static/{property_img_folder}")
    return property_img_folder


def save_images_to_temp_folder(image_files):
    """
    Generates a temporary folder for storing image files of property.
    """
    rand_dir_name = secrets.token_hex(16)
    temp_dir = rand_dir_name
    os.mkdir(f"{current_app.root_path}/base/static/property_images/{temp_dir}")

    for image_file in image_files:
        filename_hex = secrets.token_hex(10)
        checked_filename = secure_filename(image_file.filename)
        _, file_ext = os.path.splitext(checked_filename)
        checked_filename = f"{filename_hex}{file_ext}"
        image_file.save(f"{current_app.root_path}/base/static/property_images/{temp_dir}/{checked_filename}")

    return f"property_images/{temp_dir}"


def property_image_handler(temp_img_folder=None):
    """
    Handles the images uploaded from the web form. The images are down sized using
    the Pillow image library and saved to the file system. The image filenames are checked
    using the werkzeug utilities, then the filename is appended to the list of filenames.
    """
    # Delete images before before the property is updated with new images
    rand_dir_name = secrets.token_hex(16)
    save_to_folder = f"{current_app.root_path}/base/static/property_images/{rand_dir_name}"
    os.mkdir(save_to_folder)
    images_list = [f"property_images/{rand_dir_name}"]
    tmp_dir = f"{current_app.root_path}/base/static/{temp_img_folder}"

    for image_filename in os.listdir(tmp_dir):
        images_list.append(image_filename)
        image_path = f"{tmp_dir}/{image_filename}"
        image_file = Image.open(image_path)
        image_file.thumbnail((3000, 3000))
        path = f"{save_to_folder}/{image_filename}"
        image_file.save(path)

    shutil.rmtree(tmp_dir)
    return f"property_images/{rand_dir_name}", images_list


def save_profile_picture(user, form_picture):
    """
    Handle the uploaded image file. The file is renamed to a random hex and then saved
    to the static/profile_pictures folder.
    """
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_file_name = f"{user.username}{random_hex}{file_ext}"
    picture_path = os.path.join(
        current_app.root_path, "base/static/profile_pictures", picture_file_name
    )
    """
    We use the Pillow Image library to process and reduce the size of 
    the image before being saved to the file system.
    """

    img = Image.open(form_picture)
    img.thumbnail((200, 250))
    img.save(picture_path)
    user.photo = f"profile_pictures/{picture_file_name}"
    db.session.commit()
