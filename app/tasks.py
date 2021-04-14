import os
import io
from PIL import Image
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from decouple import config
from app import s3, redis_client
from config import S3_BUCKET_CONFIG, LOCAL_UPLOAD_CONFIG
from flask import current_app

celery = current_app.celery


@celery.task()
def image_process(folder_name, s3_dir):
    """
    Resize the image files, using the PIL image library
    """
    img_data = redis_client.hgetall(folder_name)
    for img_name in img_data.keys():
        byte_key_to_str = img_name.decode("utf-8")
        # Get image byte object from redis with r_key as object key
        byte_img_obj = redis_client.hget(folder_name, byte_key_to_str)
        decoded_img = Image.open(io.BytesIO(byte_img_obj))
        decoded_img.thumbnail((800, 800))
        if config("UPLOAD_CONFIG") == "AWS S3":
            # Here the byte_key_to_str is also being used filename for the image
            upload_to_s3.delay(decoded_img, s3_dir, folder_name, img_name)
        else:
            save_to_local.delay(LOCAL_UPLOAD_CONFIG, decoded_img, folder_name, img_name)


@celery.task()
def upload_to_s3(processed_img_obj, s3_dir, folder_name, img_name):
    """
    Upload to S3 and delete the image from redis.
    """
    processed_img_obj.save(img_name)  # Temporary saved before being uploaded to Amazon S3 bucket.
    # Upload to S3 and delete the image from redis.
    bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
    jpeg_extensions = [".jpg", ".jpeg"]
    _, file_ext = os.path.splitext(img_name)
    try:
        s3.upload_fileobj(
            open(img_name, "rb"),
            bucket,
            f"{s3_dir}{folder_name}/{img_name}",
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": "image/jpeg"
                if file_ext in jpeg_extensions
                else "image/png",
            },
        )
        os.remove(img_name)
        redis_client.hdel(folder_name, img_name)  # clean up by deleting in redis
        return "file uploaded"
    except Exception as err:
        print(err)


@celery.task()
def save_to_local(upload_config, processed_img_obj, folder_name, img_name):
    """
    Saves image files to the apps local storage.
    """
    processed_img_obj.save(f"{current_app.rootpath}/{upload_config['PROP_ASSETS_DIR']}/{folder_name}/{img_name}")


@celery.task()
def delete_img_obj(bucket, dir_to_del, image_list=None, filename=None):
    """
    Delete image objects stored on S3, either one object or multiple at the same time.
    """
    if image_list:
        for filename in image_list:
            s3.delete_object(Bucket=bucket, Key=dir_to_del + filename)
    else:
        s3.delete_object(Bucket=bucket, Key=dir_to_del + filename)
    return "deletion task completed"


@celery.task()
def send_email(to, subject, template, email_type):
    message = Mail(
        from_email=os.environ.get("FROM_EMAIL", config("FROM_EMAIL")),
        to_emails=to,
        subject=subject,
        html_content=template,
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY", config("SENDGRID_API_KEY")))
        sg.send(message)
        return f"A {email_type} email has been sent."
    except Exception as err:
        print(err)

