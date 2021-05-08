import os
import uuid
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
from decouple import config
from app import redis_client
from config import IMAGE_UPLOAD_CONFIG

bucket = IMAGE_UPLOAD_CONFIG["amazon_s3"]["S3_BUCKET"]
serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY", config("SECRET_KEY")))
salt = os.environ.get("SECURITY_PASSWORD_SALT", config("SECURITY_PASSWORD_SALT"))


def save_image_to_redis(image_file):
    """
    Change the filename of the uploaded image and save it temporary to redis.
    """
    _, file_extension = os.path.splitext(image_file.filename)
    new_filename = uuid.uuid4().__str__()[:8] + file_extension
    redis_client.set(new_filename, image_file.read())
    return new_filename


def generate_url_token(user_data):
    """
    Generates a url token encoded with user data.
    """
    token = serializer.dumps(user_data, salt=salt)
    return token


def confirm_token(token, expiration=3600):
    """
    Decode the data in the url token.
    """
    try:
        user_data = serializer.loads(token, salt=salt,max_age=expiration)
    except:
        return False
    return user_data


def email_verification_required(function):
    """
    This function decorator will check if the user has verified the email.
    """
    @wraps(function)
    def wrapped_func(*args, **kwargs):
        if current_user.is_verified is False:
            return redirect(url_for("base_blueprint.unverified"))
        return function
    return wrapped_func


