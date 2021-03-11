
import os
import io
from PIL import Image
from app import celery, s3, redis_client
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_prop_image_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_temp_dir = S3_BUCKET_CONFIG["TEMP_DIR"]
s3_user_image_dir = S3_BUCKET_CONFIG["USER_ASSETS"]


@celery.task()
def image_process(redis_img, upload_dir, filename):
    """
    Process image files, using the PIL image library, upload to S3 and delete the image from redis.
    """
    bytes_img = redis_client.get(redis_img)
    img = Image.open(io.BytesIO(bytes_img))
    img.thumbnail((800, 800))
    img.save(redis_img + ".jpg", format="JPEG")
    try:
        s3.upload_fileobj(
            open(redis_img + ".jpg", "rb"),  # This is the name of the file saved on line 23
            bucket,
            upload_dir + filename,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": "image/jpeg"
            }
        )
        os.remove(redis_img + ".jpg")  # Delete the file that was saved temporary on local
        redis_client.delete(redis_img)
    except Exception as err:
        return err


@celery.task()
def delete_img_obj(bucket, dir_to_del, image_list=None, filename=None):
    """
    Delete image objects stored on S3, either one object or multiple at the same time.
    """
    if image_list:
        for filename in image_list:
            s3.delete_object(
                Bucket=bucket,
                Key=dir_to_del + filename
            )
    else:
        s3.delete_object(
            Bucket=bucket,
            Key=dir_to_del + filename
        )
    return "deletion task completed"
