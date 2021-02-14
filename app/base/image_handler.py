from PIL import Image
from werkzeug.utils import secure_filename
import os
import secrets
from flask import current_app
from flask_login import current_user


def property_image_handler(image_files, save_to_folder):
    """
    Handles the docs uploaded from the web form. The docs are down sized using
    the Pillow image library and saved to the file system. The image filenames are checked
    using the werkzeug utilities, then the filename is saved to the list of filenames in the
    dictionary object.
    """
    images_list = [save_to_folder]
    for image_file in image_files:
        filename = secure_filename(image_file.filename)
        images_list.append(filename)

        image = Image.open(image_file)
        # reduce image size down to 15%
        image.thumbnail((3000, 3000))

        file_path = os.path.join(
            f"{current_app.root_path}/base/static/{save_to_folder}", filename
        )
        image.save(file_path)
    return images_list


def save_profile_picture(form_picture):
    """
    Handle the uploaded image file. The file is renamed to a random hex and then saved
    to the static/profile_pictures folder.
    """
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_file_name = f"{current_user.username}{random_hex}{file_ext}"
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

    return f"profile_pictures/{picture_file_name}"
