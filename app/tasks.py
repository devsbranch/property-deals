import json
import os
from PIL import Image
from app import celery, s3
from app.base.file_handler import update_property_images
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_prop_image_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_temp_dir = S3_BUCKET_CONFIG["TEMP_DIR"]


@celery.task()
def process_images(filename, tmp_dir, dir_to_save):
    """
    This function processes the image files, using the PIL image library. The filename argument is
    used to create writable binary object, the object is overwritten by the data of the image downloaded
    from s3 using boto3 client. Then the image processed using PIL is uploaded back to s3 using boto3 client.
    The name of this object the filename argument. The image is deleted in the temp dir for cleanup.
    """
    try:
        img_obj = open(filename, "wb")
        s3.download_fileobj(bucket, f"{s3_temp_dir + tmp_dir}{filename}", img_obj)
        pil_image_obj = Image.open(filename)
        pil_image_obj.thumbnail((800, 800))
        pil_image_obj.save(filename)

        with open(filename, "rb") as data_obj:
            s3.upload_fileobj(
                data_obj,
                bucket,
                f"{s3_prop_image_dir}{dir_to_save}{filename}",
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": "image/jpeg"
                }
            )
        os.remove(filename)
        delete_img_objs(bucket, s3_temp_dir + tmp_dir, file_obj=filename)
    except Exception as e:
        return e


@celery.task()
def update_prop_images(temp_dir, image_file_list, prop_id):
    from app.base.models import Property

    images_list = update_property_images(temp_dir, image_file_list, prop_id)
    img_list_to_json = json.dumps(images_list)
    Property.update_property_images(images_list[0], img_list_to_json, prop_id)
    return "Images Updated"


@celery.task()
def delete_img_objs(bucket, dir_to_del, image_list=None, file_obj=None):
    """
    Deletes objects on S3 either by iterating through the image_list and concatenating the
    dir_to_del and the filename in image_list to make a complete path to the object to
    be deleted or using the file_obj argument.
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
            Key=dir_to_del + file_obj
        )
    return "deletion task completed"

