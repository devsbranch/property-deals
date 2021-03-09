import json
import os
import uuid
from datetime import datetime
from PIL import Image
from flask_login import current_user
from werkzeug.utils import secure_filename
from app import db, s3
from config import S3_BUCKET_CONFIG
from app.base.models import Property

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_prop_image_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_temp_dir = S3_BUCKET_CONFIG["TEMP_DIR"]
s3_user_image_dir = S3_BUCKET_CONFIG["USER_ASSETS"]


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


def generate_img_dir_name():
    """
    This function generates a random string which is concatenated together with the current date and time, then
    returns it. This will be used by the property_image_handler() and update_property_images() function as name for
    the directory where the image files should be saved.
    """
    suffix = str(uuid.uuid4())[:15].replace("-", "")
    current_date = datetime.utcnow()
    time, date = (
        current_date.strftime("%H-%M-%S"),
        current_date.strftime("%d-%B-%Y"),
    )
    dir_name = f"{suffix}_{date}_{time}/"
    return dir_name


def property_image_handler(temp_dir, image_file_list):
    """
    Save the images. First a new directory is created where the images are saved. The process_images() is called and
    runs in the background. Then the directory name and image filenames are returned in one list.
    """

    from app.tasks import process_images

    generated_dirname = generate_img_dir_name()
    images_list = [generated_dirname]
    for filename in image_file_list:
        images_list.append(filename)
        process_images.delay(filename, temp_dir, generated_dirname)
    return images_list


def update_property_images(temp_dir, image_file_list, prop_id):
    """
    Updates the images. First the old directory is deleted and then a new one is created
    where the images are saved. The process_images() is called and runs in the background.
    Then the directory name and image filenames are returned in one list.
    """
    from app.tasks import process_images, delete_img_objs

    prop_to_update = Property.query.get(prop_id)
    prop_images = json.loads(prop_to_update.photos)
    path_to_del = s3_prop_image_dir + prop_to_update.image_folder
    delete_img_objs.delay(bucket, path_to_del, prop_images)

    generated_dir_name = generate_img_dir_name()

    images_list = [generated_dir_name]
    for filename in image_file_list:
        images_list.append(filename)
        process_images.delay(filename, temp_dir, generated_dir_name)
    return images_list


def save_profile_picture(image_file):
    """
    Handle the uploaded image file. The file is renamed to a random hex, then the image object is process by PIL
    image library then saved.
    """
    from app.tasks import update_profile_image

    dir_name = generate_img_dir_name()
    _, file_ext = os.path.splitext(image_file.filename)
    image_filename = f"{str(uuid.uuid4())[:8]}{file_ext}"

    img = Image.open(image_file)
    img.thumbnail((200, 250))
    img.save(image_filename)
    current_user.photo = s3_user_image_dir + dir_name + image_filename
    db.session.commit()

    content_type = image_file.content_type
    update_profile_image.delay(dir_name, image_filename, content_type)
