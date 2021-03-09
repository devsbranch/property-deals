import json
import os
import uuid
import calendar
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
from app import db, s3
from config import S3_BUCKET_CONFIG
from app.base.models import Property

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_prop_image_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_temp_dir = S3_BUCKET_CONFIG["TEMP_DIR"]


def save_images_to_temp_folder(image_files):
    """
    Creates a temporary folder for storing image objects and returns
    name of the temporary folder and the list of the filenames that were saved to S3 in the
    same folder.
    """
    dir_name = str(uuid.uuid4())[:8] + "/"

    image_list = []
    for image_file in image_files:
        random_str = str(uuid.uuid4())[:13].replace("-", "")
        checked_filename = secure_filename(image_file.filename)
        _, file_ext = os.path.splitext(checked_filename)  # get file extension
        clean_filename = f"{random_str}{file_ext}"
        image_list.append(clean_filename)
        try:
            s3.upload_fileobj(
                image_file,
                bucket,
                f"{s3_temp_dir}{dir_name}{clean_filename}",
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": image_file.content_type
                }
            )
        except Exception as e:
            return e

    return dir_name, image_list


def generate_prop_img_dir_name():
    suffix = str(uuid.uuid4())
    current_date = datetime.utcnow()
    time, date = (
        current_date.strftime("%H-%M-%S"),
        current_date.strftime("%d-%B-%Y"),
    )
    dir_name = f"property_{suffix[:13]}_{date}_{time}/"
    return dir_name


def save_property_data(form_data, temp_dir, image_file_list):
    from app.base.models import Property

    images_list = property_image_handler(temp_dir, image_file_list)
    img_list_to_json = json.dumps(images_list)
    prop_images = {"photos": img_list_to_json, "image_folder": images_list[0]}
    form_data.update(prop_images)
    Property.add_property(form_data)
    return "Property Created"


def property_image_handler(temp_dir, image_file_list):
    from app.tasks import process_images
    generated_dirname = generate_prop_img_dir_name()
    images_list = [generated_dirname]
    for filename in image_file_list:
        images_list.append(filename)
        process_images.delay(filename, temp_dir, generated_dirname)
    return images_list


def update_property_images(temp_dir, image_file_list, prop_id):
    from app.tasks import process_images, delete_img_objs

    prop_to_update = Property.query.get(prop_id)
    prop_images = json.loads(prop_to_update.photos)
    path_to_del = s3_prop_image_dir + prop_to_update.image_folder
    delete_img_objs.delay(bucket, path_to_del, prop_images)

    generated_dir_name = generate_prop_img_dir_name()

    images_list = [generated_dir_name]
    for filename in image_file_list:
        images_list.append(filename)
        process_images.delay(filename, temp_dir, generated_dir_name)
    return images_list


def save_profile_picture(user, form_picture):
    """
    Handle the uploaded image file. The file is renamed to a random hex and then saved
    to the static/profile_pictures folder.
    """
    current_date = datetime.utcnow()
    time, date, month_name = (
        current_date.strftime("%H:%M:%S"),
        current_date.strftime("%d-%m-%Y"),
        calendar.month_name[int(current_date.strftime("%m"))],
    )
    timestamped_dir_name = f"image_{time}-{month_name}-{date}"
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_file_name = f"{user.username}{timestamped_dir_name}{file_ext}"
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
