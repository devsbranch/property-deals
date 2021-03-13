import os
import io
from PIL import Image
from app import celery, s3, redis_client
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]


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
        decoded = Image.open(io.BytesIO(byte_img_obj))
        decoded.thumbnail((800, 800))
        decoded.save(byte_key_to_str)
        upload_to_s3.delay(byte_key_to_str, s3_dir, folder_name)


@celery.task()
def upload_to_s3(img_obj, s3_dir, folder_name):
    """
    Upload to S3 and delete the image from redis.
    """
    jpeg_extensions = [".jpg", ".jpeg"]
    _, file_ext = os.path.splitext(img_obj)
    try:
        s3.upload_fileobj(
            open(img_obj, "rb"),
            bucket,
            f"{s3_dir}{folder_name}/{img_obj}",
            ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg" if file_ext in jpeg_extensions else "image/png"}
        )
        os.remove(img_obj)
        redis_client.hdel(folder_name, img_obj)  # clean up by deleting in redis
        return "file uploaded"
    except Exception as err:
        return err


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

