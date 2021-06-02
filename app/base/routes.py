import pdb
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, UserProfileUpdateForm
from app.base.models import User
from app.base.utils import save_image_to_redis, generate_url_token, confirm_token
from app.tasks import profile_image_process, delete_profile_image, send_email
from config import IMAGE_UPLOAD_CONFIG


aws_s3_bucket_name = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"]
s3_image_url = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_URL"]
aws_bucket_name = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"]
profile_image_upload_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "USER_PROFILE_IMAGES"
]
cover_image_upload_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "USER_COVER_IMAGES"
]
image_server_config = IMAGE_UPLOAD_CONFIG["STORAGE_LOCATION"]


email_template_vars = {
    "email_verify": {
        "subject": "Verify Email - Property Deals",
        "msg_header": "Verify Your Email",
        "msg_body": "Please verify your email address to be able to list your Property on Property Deals.",
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


def user_data_for_url_token(username, email, phone, email_category=None):
    user_data = {
        "username": username,
        "email": email,
        "phone": phone,
        "email_category": email_category,
    }
    return user_data


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("errors/403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("errors/403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/feedback")
def feedback():
    return render_template("feedback.html")


# Login & Registration
@blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()

        # Check the password
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home_blueprint.index"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("accounts/login.html", form=form)


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = CreateAccountForm()
    if form.validate_on_submit():
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        user_data = user_data_for_url_token(
            form.username.data,
            form.email.data,
            form.phone.data,
            email_category="Verify Email",
        )
        token = generate_url_token(user_data)
        confirm_url = url_for(
            "base_blueprint.verify_email", token=token, _external=True
        )
        template_text = email_template_vars["email_verify"]
        msg_header = template_text["msg_header"]
        msg_body = template_text["msg_body"]
        subject = template_text["subject"]
        email_template = render_template(
            "email_template.html",
            confirm_url=confirm_url,
            name=f"{form.first_name.data} {form.last_name.data}",
            html_msg_header=msg_header,
            html_msg_body=msg_body,
            button_text=template_text["btn_txt"],
        )
        send_email.delay(form.email.data, subject, email_template)
        flash(
            "Your account has been created. Check your inbox to verify your email.",
            "success",
        )
        return redirect(url_for("base_blueprint.login"))

    return render_template("accounts/register.html", form=form)


@blueprint.route("/verify_email/<token>")
def verify_email(token):
    user_data = confirm_token(token)
    if not user_data or user_data["email_category"] != "Verify Email":
        flash("The confirmation email is invalid or has expired")
        return redirect(url_for("home_blueprint.index"))
    user = User.query.filter_by(email=user_data["email"]).first()
    if user.is_verified:
        flash("Your email is already verified")
    else:
        user.is_verified = True
        user.date_confirmed = datetime.now()
        db.session.commit()
        flash("Your email has been verified.", "success")
        return redirect(url_for("home_blueprint.index"))


@blueprint.route("/resend")
@login_required
def resend_verification_email():
    from app.tasks import send_email

    user_data = user_data_for_url_token(
        current_user.email, current_user.phone, email_category="Verify Email"
    )
    token = generate_url_token(user_data)
    confirm_url = url_for("base_blueprint.verify_email", token=token, _external=True)
    template_text = email_template_vars["email_verify"]
    msg_header = template_text["msg_header"]
    msg_body = template_text["msg_body"]
    subject = template_text["subject"]
    email_template = render_template(
        "email_template.html",
        url=confirm_url,
        name=f"{current_user.first_name} {current_user.last_name}",
        html_msg_header=msg_header,
        html_msg_body=msg_body,
        button_text=template_text["btn_txt"],
    )
    send_email.delay(current_user.email, subject, email_template)
    flash("A new verification email has been sent", "success")
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/unverified")
@login_required
def unverified():
    if current_user.is_verified:
        flash("Your email is already verified", "success")
        return redirect(url_for("home_blueprint.index"))
    flash("You need to verify your email first", "warning")
    return render_template("unverified.html")


@blueprint.route("/my_profile", methods=["GET", "POST"])
@login_required
def user_profile():
    form = UserProfileUpdateForm(obj=current_user)
    if request.method == "POST" and form.validate_on_submit():
        if (
            request.files.get("profile_photo").filename != ""
        ):  # Check if a profile image has been uploaded
            # Delete the previous profile image if it exists
            delete_profile_image.delay(
                profile_image_upload_dir,
                current_user.profile_photo,
                s3_bucket_name=aws_s3_bucket_name,
            )
            file = request.files.get("profile_photo")
            filename = save_image_to_redis(file)
            profile_image_process.delay(filename, photo_type="profile")
            current_user.profile_photo = filename
            current_user.prof_photo_loc = image_server_config

        if (
            request.files.get("cover_photo").filename != ""
        ):  # Check if a cover image has been uploaded
            # Delete the previous profile image if it exists
            delete_profile_image.delay(
                cover_image_upload_dir,
                current_user.cover_photo,
                s3_bucket_name=aws_s3_bucket_name,
            )
            file = request.files.get("cover_photo")
            filename = save_image_to_redis(file)
            profile_image_process.delay(filename, photo_type="cover")
            current_user.cover_photo = filename
            current_user.cover_photo_loc = image_server_config

        for key, value in request.form.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]
            if key == "password":  # Check if password is in the form
                if value:
                    value = generate_password_hash(
                        value
                    )  # Hash the password from the form
                else:
                    # Maintain the old user's password in the database if password was not in form
                    value = current_user.password

            setattr(current_user, key, value)
        db.session.commit()
        flash("Your account information has been updated.", "success")
        return redirect(url_for("base_blueprint.user_profile", user_id=current_user.id))

    elif request.method == "GET":
        # Populates the form fields with user data.
        form.populate_obj(current_user)
    return render_template(
        "accounts/settings.html",
        form=form,
        s3_image_url=s3_image_url,
        profile_image_dir=profile_image_upload_dir,
        cover_image_dir=cover_image_upload_dir,
    )


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/shutdown")
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("errors/403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("errors/403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("erros/404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500
