import os
import io
import shutil
import json
from pathlib import Path
from flask import current_app
from PIL import Image
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app import s3, redis_client
from config import IMAGE_UPLOAD_CONFIG

celery = current_app.celery
aws_bucket_name = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"]
profile_image_upload_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "USER_PROFILE_IMAGES"
]
cover_image_upload_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "USER_COVER_IMAGES"
]
temp_image_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["TEMP_DIR"]
property_listing_images_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "PROPERTY_LISTING_IMAGES"
]
image_server_config = IMAGE_UPLOAD_CONFIG["STORAGE_LOCATION"]


@celery.task()
def profile_image_process(image_name, photo_type=None):
    """
    Resize the image file using the PIL image library and save it to the app server or
    Amazon S3 depending on the configuration.
    """
    temp_image_path = Path(f"{current_app.root_path}/base/static/{temp_image_dir}")

    img_data = redis_client.get(
        image_name
    )  # get image from redis using image_name as the key
    decoded_img = Image.open(io.BytesIO(img_data))
    decoded_img.thumbnail((800, 800))
    decoded_img.save(
        f"{temp_image_path}/{image_name}"
    )  # save the resized image to the temporary folder

    if image_server_config == "app_server_storage":
        profile_image_upload_path = Path(
            f"{current_app.root_path}/base/static/{profile_image_upload_dir}"
        )
        cover_image_upload_path = Path(
            f"{current_app.root_path}/base/static/{cover_image_upload_dir}"
        )

        if photo_type == "profile":
            shutil.copyfile(
                f"{temp_image_path}/{image_name}",
                f"{profile_image_upload_path}/{image_name}",
            )
        else:
            shutil.copyfile(
                f"{temp_image_path}/{image_name}",
                f"{cover_image_upload_path}/{image_name}",
            )
        os.remove(
            f"{temp_image_path}/{image_name}"
        )  # Clean up by deleting the image in the temporary folder
        redis_client.delete(image_name)  # Clean up by deleting the image in redis
    elif image_server_config == "amazon_s3":
        # Upload the image to Amazon S3 if the configuration is set to "amazon_s3"
        profile_image_upload_to_S3.delay(
            image_name, profile_image_upload_dir
        ) if photo_type == "profile" else profile_image_upload_to_S3.delay(
            image_name, cover_image_upload_dir
        )


@celery.task()
def profile_image_upload_to_S3(image_name, destination_dir):
    """
    Upload the image to Amazon S3.
    """
    # Full path where the image is stored temporary
    temp_image_path = Path(f"{current_app.root_path}/base/static/{temp_image_dir}")

    jpeg_extensions = [".jpg", ".jpeg"]
    _, file_ext = os.path.splitext(image_name)

    try:
        s3.upload_fileobj(
            open(f"{temp_image_path}/{image_name}", "rb"),
            aws_bucket_name,
            f"{destination_dir}{image_name}",
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": "image/jpeg"
                if file_ext in jpeg_extensions
                else "image/png",
            },
        )
        os.remove(
            f"{temp_image_path}/{image_name}"
        )  # Clean up by deleting the image in the temporary folder
        redis_client.delete(image_name)  # Clean up by deleting the image in redis
        return "file uploaded"
    except Exception as err:
        print(err)


@celery.task()
def delete_profile_image(image_path, image_filename, s3_bucket_name=None):
    """
    Deletes the image stored on the app server or on Amazon S3 depending on the configuration.
    """
    if image_server_config == "amazon_s3":
        s3.delete_object(Bucket=s3_bucket_name, Key=f"{image_path}{image_filename}")
    elif image_server_config == "app_server_storage":
        try:
            path_to_image = Path(
                f"{current_app.root_path}/base/static/{image_path}/{image_filename}"
            )
            os.remove(path_to_image)
        except FileNotFoundError:
            pass
    return "deletion task completed"


@celery.task()
def send_email(to, subject, template):
    message = Mail(
        from_email=os.environ.get("FROM_EMAIL", config("FROM_EMAIL")),
        to_emails=to,
        subject=subject,
        html_content=template,
    )
    try:
        sg = SendGridAPIClient(
            os.environ.get("SENDGRID_API_KEY", config("SENDGRID_API_KEY"))
        )
        sg.send(message)
    except Exception as err:
        print(err)


@celery.task()
def process_property_listing_images(redis_img_dict_key):
    """
    Resize the image file using the PIL image library and save it to the app server or
    Amazon S3 depending on the configuration. Since a property listing has many images, a
    directory is created with redis_img_dict_key as the directory name where the image files
    are saved.
    """
    temp_image_path = Path(f"{current_app.root_path}/base/static/{temp_image_dir}")
    redis_images = redis_client.hgetall(redis_img_dict_key)
    folder_to_save_image = Path(
        f"{current_app.root_path}/base/static/{property_listing_images_dir}{redis_img_dict_key}"
    )
    folder_to_save_image.mkdir(parents=True, exist_ok=True)

    for image_filename in redis_images.keys():
        image_filename = image_filename.decode("utf-8")
        image_file = redis_client.hget(redis_img_dict_key, image_filename)
        image_obj = Image.open(io.BytesIO(image_file))
        image_obj.thumbnail((800, 800))
        image_obj.save(
            f"{current_app.root_path}/base/static/{temp_image_dir}{image_filename}"
        )

        if image_server_config == "app_server_storage":
            shutil.copyfile(
                f"{temp_image_path}/{image_filename}",
                f"{folder_to_save_image}/{image_filename}",
            )
            os.remove(
                f"{temp_image_path}/{image_filename}"
            )  # Clean up by deleting the image in the temporary folder
            redis_client.hdel(
                redis_img_dict_key, image_filename
            )  # Clean up by deleting the image in redis
        elif image_server_config == "amazon_s3":
            # Upload the image to Amazon S3 if the configuration is set to "amazon_s3"
            property_image_upload_to_S3.delay(image_filename, redis_img_dict_key)


@celery.task()
def property_image_upload_to_S3(image_name, redis_img_dict_key):
    """
    Upload the image to Amazon S3.
    """
    # Full path where the image is stored temporary
    temp_image_path = Path(f"{current_app.root_path}/base/static/{temp_image_dir}")

    jpeg_extensions = [".jpg", ".jpeg"]
    _, file_ext = os.path.splitext(image_name)

    try:
        s3.upload_fileobj(
            open(f"{temp_image_path}/{image_name}", "rb"),
            aws_bucket_name,
            # redis_images_key is used as a name for the folder where images will be saved
            f"{property_listing_images_dir}{redis_img_dict_key}/{image_name}",
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": "image/jpeg"
                if file_ext in jpeg_extensions
                else "image/png",
            },
        )
        os.remove(
            f"{temp_image_path}/{image_name}"
        )  # Clean up by deleting the image in the temporary folder
        redis_client.hdel(
            redis_img_dict_key, image_name
        )  # Clean up by deleting the image in redis
        return "file uploaded"
    except Exception as err:
        print(err)


@celery.task()
def delete_property_listing_images(images_location, image_path, images_folder, images_list, s3_bucket_name=None):
    """
    Deletes the image stored on the app server or on Amazon S3 depending on the configuration.
    """

    if images_location == "amazon_s3":
        for image_name in images_list[1:]:
            s3.delete_object(Bucket=s3_bucket_name, Key=f"{image_path}{images_folder}{image_name}")
    elif images_location == "app_server_storage":
        try:
            path_to_image = Path(
                f"{current_app.root_path}/base/static/{image_path}/{images_folder}"
            )
            shutil.rmtree(path_to_image)
        except FileNotFoundError as error:
            print(error)
    return "deletion task completed"
