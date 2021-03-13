import os
import uuid
import numpy as np
from datetime import datetime
from app import redis_client
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]


def generate_dir_name(username):
    """
    This function generates a random string to be used as a directory name where images will be saved on S3
    """
    suffix = uuid.uuid4().__str__()[:5].replace("-", "")
    current_date = datetime.utcnow()
    time, date = (
        current_date.strftime("%H"),
        current_date.strftime("%d-%m-%Y"),
    )
    dir_name = f"{username}_{date}_{time}_{suffix}"
    return dir_name


def save_to_redis(image_file_list, username):
    """
    Create a dictionary which will contain folder_name as key and random_img_name/img_to_bytes as value then push to redis.
    to redis.
    """
    folder_name = generate_dir_name(username)
    img_dict = {}
    for file in image_file_list:
        _, file_ext = os.path.splitext(file.filename)  # Get file extension
        new_img_name = uuid.uuid4().__str__()[:8]  # generate a random string to set as key for the image in img_dict
        # convert file to bytes
        img_to_bytes = np.array(np.frombuffer(file.read(), np.uint8)).tobytes()
        img_dict[f"{new_img_name}{file_ext}"] = img_to_bytes
    redis_client.hmset(folder_name, img_dict)
    return folder_name
