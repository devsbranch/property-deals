import os
import uuid
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

