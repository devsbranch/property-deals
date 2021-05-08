import os
import io
import shutil
from pathlib import Path
from flask import current_app
from PIL import Image
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app import s3, redis_client
from config import IMAGE_UPLOAD_CONFIG

celery = current_app.celery
aws_bucket_name = IMAGE_UPLOAD_CONFIG["amazon_s3"]["S3_BUCKET"]
profile_image_upload_dir = IMAGE_UPLOAD_CONFIG["image_save_directories"]["USER_PROFILE_IMAGES"]
cover_image_upload_dir = IMAGE_UPLOAD_CONFIG["image_save_directories"]["USER_COVER_IMAGES"]
temp_image_dir = IMAGE_UPLOAD_CONFIG["image_save_directories"]["TEMP_DIR"]
image_server_config = IMAGE_UPLOAD_CONFIG["storage_location"]


@celery.task()
def profile_image_process(image_name, photo_type=None):
    """
    Resize the image file using the PIL image library and save it to to the app server or
    AmazonS3 depending on the configuration.
    """
    temp_image_path = Path(f"{current_app.root_path}/base/static/{temp_image_dir}")

    img_data = redis_client.get(image_name)  # get image from redis using image_name as the key
    decoded_img = Image.open(io.BytesIO(img_data))
    decoded_img.thumbnail((800, 800))
    if not temp_image_path.exists():
        # Create a temporary folder to save the resized image.
        temp_image_path.mkdir(parents=True, exist_ok=True)
    decoded_img.save(f"{temp_image_path}/{image_name}")  # save the resized image to the temporary folder

    if image_server_config == "app_server_storage":
        profile_image_upload_path = Path(f"{current_app.root_path}/base/static/{profile_image_upload_dir}")
        cover_image_upload_path = Path(f"{current_app.root_path}/base/static/{cover_image_upload_dir}")

        # Check if the folders exists
        if not profile_image_upload_path.exists() or not cover_image_upload_path.exists():
            # Create a folder to store the resized image to be copied from the temporary folder.
            profile_image_upload_path.mkdir(parents=True, exist_ok=True)
            cover_image_upload_path.mkdir(parents=True, exist_ok=True)
        if photo_type == "profile":
            shutil.copyfile(f"{temp_image_path}/{image_name}",
                            f"{profile_image_upload_path}/{image_name}"
                            )
        else:
            shutil.copyfile(f"{temp_image_path}/{image_name}",
                            f"{cover_image_upload_path}/{image_name}"
                            )
        os.remove(f"{temp_image_path}/{image_name}")  # Clean up by deleting the image in the temporary folder
        redis_client.delete(image_name)  # Clean up by deleting the image in redis
    elif image_server_config == "amazon_s3":
        # Upload the image to Amazon S3 if the configuration is set to "amazon_s3"
        profile_image_upload_to_S3.delay(image_name, profile_image_upload_dir) if photo_type == "profile" else profile_image_upload_to_S3.delay(image_name, cover_image_upload_dir)


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
        os.remove(f"{temp_image_path}/{image_name}")  # Clean up by deleting the image in the temporary folder
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
        path_to_image = Path(f"{current_app.root_path}/base/static/{image_path}/{image_filename}")
        if path_to_image.exists():
            os.remove(path_to_image)
        else:
            pass
    return "deletion task completed"


@celery.task()
def send_email(to, subject, template):
    message = Mail(
        from_email=os.environ.get("FROM_EMAIL", config("FROM_EMAIL")),
        to_emails=to,
        subject=subject,
        html_content=template
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY", config("SENDGRID_API_KEY")))
        sg.send(message)
    except Exception as err:
        print(err)
