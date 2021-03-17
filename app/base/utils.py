import os
import uuid
import numpy as np
from datetime import datetime
from functools import wraps
from flask import redirect, url_for
from itsdangerous import URLSafeTimedSerializer
from flask_login import current_user
from app import redis_client
from config import S3_BUCKET_CONFIG

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
salt = os.environ.get("SECURITY_PASSWORD_SALT")


def generate_url_token(user_data):
    """
    Generates a token and with user email as encoded data
    """
    token = serializer.dumps(user_data, salt=salt)
    return token


def confirm_token(token, expiration=3600):
    """
    Decodes the data in the token, return False if token is not valid or has expired and return
    decoded data if token is valid.
    """
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
    except:
        return False
    return email


def email_verification_required(function):
    """
    Checks if the user email has been verified
    """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.is_verified is False:
            return redirect(url_for("base_blueprint.unverified"))
        return function(*args, **kwargs)

    return decorated_function


def generate_confirmation_token(user_email):
    """
    Generates a token and with user email as encoded data
    """
    serializer = URLSafeTimedSerializer(
        os.environ.get("SECRET_KEY")
    )
    salt = os.environ.get("SECURITY_PASSWORD_SALT")
    token = serializer.dumps(user_email, salt=salt)
    return token


def confirm_token(token, expiration=3600):
    """
    Decodes the data in the token, return False if token is not valid or has expired and return
    decoded data if token is valid.
    """
    serializer = URLSafeTimedSerializer(
        os.environ.get("SECRET_KEY")
    )
    salt = os.environ.get("SECURITY_PASSWORD_SALT")
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
    except:
        return False
    return email


def email_verification_required(function):
    """
    Checks if the user email has been verified
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.is_verified is False:
            return redirect(url_for("base_blueprint.unverified"))
        return function(*args, **kwargs)

    return decorated_function


def generate_confirmation_token(user_email):
    """
    Generates a token and with user email as encoded data
    """
    serializer = URLSafeTimedSerializer(
        os.environ.get("SECRET_KEY")
    )
    salt = os.environ.get("SECURITY_PASSWORD_SALT")
    token = serializer.dumps(user_email, salt=salt)
    return token


def confirm_token(token, expiration=3600):
    """
    Decodes the data in the token, return False if token is not valid or has expired and return
    decoded data if token is valid.
    """
    serializer = URLSafeTimedSerializer(
        os.environ.get("SECRET_KEY")
    )
    salt = os.environ.get("SECURITY_PASSWORD_SALT")
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
    except:
        return False
    return email


def email_verification_required(function):
    """
    Checks if the user email has been verified
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.is_verified is False:
            return redirect(url_for("base_blueprint.unverified"))
        return function(*args, **kwargs)

    return decorated_function


def generate_dir_name(username):
    """
    This function generates a random string to be used as a directory name where images will be saved on S3
    """
    suffix = uuid.uuid4().__str__()[:5]
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
        new_img_name = uuid.uuid4().__str__()[
            :8
        ]  # generate a random string to set as key for the image in img_dict
        # convert file to bytes
        img_to_bytes = np.array(np.frombuffer(file.read(), np.uint8)).tobytes()
        img_dict[f"{new_img_name}{file_ext}"] = img_to_bytes
    redis_client.hmset(folder_name, img_dict)
    return folder_name
