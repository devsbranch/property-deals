import os
import uuid
from functools import wraps
from flask import redirect, url_for, render_template
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
from decouple import config
from app import redis_client
from config import IMAGE_UPLOAD_CONFIG

bucket = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"]
serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY", config("SECRET_KEY")))
salt = os.environ.get("SECURITY_PASSWORD_SALT", config("SECURITY_PASSWORD_SALT"))

email_template_vars = {
    "verify_email": {
        "subject": "Verify Email - Property Deals",
        "msg_header": "Verify Your Email",
        "msg_body": """Thanks for signing up. Please verify your email address to be able to list your Property 
                    on Property Deals.""",
        "btn_txt": "Verify Email",
    },
    "password_reset": {
        "subject": "Reset Password - Property Deals",
        "msg_header": "Password Reset",
        "msg_body": """You are receiving this email because you requested a password reset. 
                    If you didn't request a password reset, kindly ignore this email.""",
        "btn_txt": "Reset Password",
    },
}


def user_data_for_url_token(username, email, email_category=None):
    user_data = {
        "username": username,
        "email": email,
        "email_category": email_category,
    }
    return user_data


def generate_url_and_email_template(
    email, username, first_name, last_name, email_category=None
):
    user_data = user_data_for_url_token(username, email, email_category=email_category)
    token = generate_url_token(user_data)
    generated_url = url_for(
        f"base_blueprint.{email_category}", token=token, _external=True
    )
    template_text = email_template_vars[email_category]
    msg_header = template_text["msg_header"]
    msg_body = template_text["msg_body"]
    subject = template_text["subject"]
    email_template = render_template(
        "email_template.html",
        url=generated_url,
        name=f"{first_name} {last_name}",
        html_msg_header=msg_header,
        html_msg_body=msg_body,
        button_text=template_text["btn_txt"],
    )
    return email_template, subject


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
        user_data = serializer.loads(token, salt=salt, max_age=expiration)
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
        return function(*args, **kwargs)

    return wrapped_func


def check_account_status(function):
    @wraps(function)
    def wrapped_func(*args, **kwargs):
        try:
            if current_user.acc_deactivated is True:
                return redirect(url_for("base_blueprint.deactivated_acc_page"))
        # Catch attribute error since anonymous(logged out) user does not have current_user.acc_deactivated attribute
        except AttributeError:
            pass
        return function(*args, **kwargs)

    return wrapped_func


def save_property_listing_images_to_redis(image_files):
    """
    Saves the image files to redis in a hash map. The image_files_redis_key will be used to get the images in redis
    for resizing. The image_files_redis_key will also be used a folder name where the processed images will be saved.
    """
    image_files_redis_key = uuid.uuid4().__str__()[:15].replace("-", "")
    image_data_dict = {}
    for image_file in image_files:
        _, file_extension = os.path.splitext(image_file.filename)
        new_image_filename = uuid.uuid4().__str__()[:8]
        image_data_dict[f"{new_image_filename}{file_extension}"] = image_file.read()
    redis_client.hmset(image_files_redis_key, image_data_dict)
    return image_files_redis_key
