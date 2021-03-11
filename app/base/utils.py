import uuid
import numpy as np
from datetime import datetime
from app import redis_client
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_prop_image_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_user_image_dir = S3_BUCKET_CONFIG["USER_ASSETS"]


def generate_dir_name():
    """
    This function generates a random string tobe used as a directory name where images will be saved on S3
    """
    suffix = str(uuid.uuid4())[:15].replace("-", "")
    current_date = datetime.utcnow()
    time, date = (
        current_date.strftime("%H-%M-%S"),
        current_date.strftime("%d-%B-%Y"),
    )
    dir_name = f"{suffix}_{date}_{time}/"
    return dir_name


def save_to_redis(image_file_list):
    """
    Saves the images to redis by converting it to bytes. Returns the keys of each imagein a list.
    """
    redis_img_keys = []
    for file in image_file_list:
        rand_str = str(uuid.uuid4())[:8]  # generate a random string to set as key for the object in redis
        redis_img_keys.append(rand_str)
        # convert file to bytes
        img_to_bytes = np.array(np.frombuffer(file.read(), np.uint8)).tobytes()
        redis_client.set(rand_str, img_to_bytes)
    return redis_img_keys


def resize_images(key_list, upload_dir):
    from app.tasks import image_process

    filenames = [upload_dir]  # will contain list of image filenames in the destination folder
    for r_key in key_list:
        rand_str = str(uuid.uuid4())[:8] + ".jpg"  # will be used as filename for the file when uploading to S3
        image_process.delay(r_key, s3_prop_image_dir + upload_dir, rand_str)  # uploads the image file to S3
        filenames.append(rand_str)
    return filenames
