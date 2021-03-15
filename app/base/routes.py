# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager, redis_client
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, UpdateAccountForm, RequestResetPasswordForm, ResetPasswordForm
from app.base.models import User
from app.base.utils import save_to_redis, generate_url_token, confirm_token
from config import S3_BUCKET_CONFIG

s3_url = S3_BUCKET_CONFIG["S3_URL"]
s3_bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_user_img_dir = S3_BUCKET_CONFIG["USER_ASSETS"]

"""
Collection of email messages for email verification and password reset.
Makes it easy to use one html template
"""
email_msg = {
    "email_verify": {
        "subject": "Verify Email - Property Deals",
        "msg_header": "Verify Your Email",
        "msg_body": "Thank you for signing up on Property deals. Click on the button below to verify your email",
        "btn_txt": "Verify"
    },
    "password_reset": {
        "subject": "Reset Password - Property Deals",
        "msg_header": "Password Reset",
        "msg_body": """You are receiving this email because you requested a password reset. 
                    If you didn't request a password reset, kindly ignore this email.""",
        "btn_txt": "Reset Password"
    }
}


def user_data_to_generate_token(email, email_type):
    user_data = {
        "email": email,
        "email_type": email_type
    }
    return user_data


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/errors-<errors>")
def route_errors(error):
    return render_template("errors/{}.html".format(error))


@blueprint.route("/verify_email/<token>")
def verify_email(token):
    user_data = confirm_token(token)
    if not user_data or user_data["email_type"] != "verify_email":
        flash("The confirmation email is invalid or has expired.", "danger")
        return redirect(url_for("home_blueprint.index"))
    user = User.query.filter_by(email=user_data["email"]).first()
    if user.is_verified:
        flash("Your email is already verified.", "success")
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
    user_data = user_data_to_generate_token(current_user.email, "verify_email")
    token = generate_url_token(user_data)

    confirm_url = url_for("base_blueprint.verify_email", token=token, _external=True)
    template_txt = email_msg["email_verify"]
    msg_header = template_txt["msg_header"]
    msg_body = template_txt["msg_body"]
    subject = template_txt["subject"]
    template = render_template(
        "email_template.html",
        url=confirm_url,
        name=f"{current_user.first_name} {current_user.last_name}",
        html_msg_header=msg_header,
        html_msg_body=msg_body,
        btn_txt=template_txt["btn_txt"]
    )
    send_email.delay(current_user.email, subject, template, "verification")
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
            user.is_active = True
            login_user(user)
            return redirect(url_for("home_blueprint.index"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("accounts/login.html", form=form)


@blueprint.route('/request-password-reset', methods=["GET", "POST"])
def request_password_reset():
    from app.tasks import send_email
    form = RequestResetPasswordForm()

    if current_user.is_authenticated:
        logout_user()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        user_data = user_data_to_generate_token(user.email, "password_reset")
        token = generate_url_token(user_data)

        reset_pass_url = url_for("base_blueprint.reset_password", token=token, _external=True)
        template_txt = email_msg["password_reset"]
        msg_header = template_txt["msg_header"]
        msg_body = template_txt["msg_body"]
        subject = template_txt["subject"]
        template = render_template(
            "email_template.html",
            url=reset_pass_url,
            name=f"{user.first_name} {user.last_name}",
            html_msg_header=msg_header,
            html_msg_body=msg_body,
            btn_txt=template_txt["btn_txt"]
        )
        send_email.delay(user.email, subject, template, "password reset")
        flash("An link to reset you password has been sent to your email.", "success")
        return redirect(url_for("home_blueprint.index"))
    return render_template("request_reset_pass.html", form=form)


@blueprint.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()

    if current_user.is_authenticated:
        return redirect(url_for("home_blueprint.index"))
    user_data = confirm_token(token)
    if not user_data or user_data["email_type"] != "password_reset":
        flash("The link is invalid or has expired.", "danger")
        return redirect(url_for("home_blueprint.index"))
    user = User.query.filter_by(email=user_data["email"]).first()

    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Your password has been reset")
        return redirect(url_for("base_blueprint.login"))
    return render_template("reset_password.html", form=form)


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    from app.tasks import send_email

    form = CreateAccountForm()
    if request.method == "POST" and form.validate_on_submit():
        user_data = {
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "other_name": form.other_name.data,
            "gender": form.gender.data,
            "address_1": form.address_1.data,
            "address_2": form.address_2.data,
            "city": form.city.data,
            "state": form.state.data,
            "postal_code": form.postal_code.data,
            "phone_number": form.phone_number.data,
            "username": form.username.data,
            "email": form.email.data,
            "password": generate_password_hash(form.password.data),
        }
        User.add_user(user_data)
        user_data = user_data_to_generate_token(form.email.data, "verify_email")
        token = generate_url_token(user_data)
        confirm_url = url_for("base_blueprint.verify_email", token=token, _external=True)
        template_txt = email_msg["email_verify"]
        msg_header = template_txt["msg_header"]
        msg_body = template_txt["msg_body"]
        subject = template_txt["subject"]
        template = render_template(
            "email_template.html",
            url=confirm_url,
            name=f"{form.first_name.data} {form.last_name.data}",
            html_msg_header=msg_header,
            html_msg_body=msg_body,
            btn_txt=template_txt["btn_txt"]
        )
        send_email.delay(form.email.data, subject, template, "verification")
        flash("A verification email has been sent", "success")
        return redirect(url_for("base_blueprint.login"))

    return render_template("accounts/register.html", form=form)


@blueprint.route("/account", methods=["GET", "POST"])
@login_required
def account():
    from app.tasks import image_process, delete_img_obj

    user_id = current_user.id
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            # delete previous profile image
            delete_img_obj.delay(
                s3_bucket, s3_user_img_dir, filename=current_user.photo
            )

            image = request.files["picture"]
            folder_name = save_to_redis([image], current_user.username)

            image_process.delay(folder_name, s3_user_img_dir)
            image_names = redis_client.hgetall(folder_name)
            image_list = [
                f"{image_name.decode('utf-8')}" for image_name in image_names.keys()
            ]

            current_user.photo = f"{folder_name}/{image_list[0]}"
            db.session.commit()

        user_data = {
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "other_name": form.other_name.data,
            "gender": form.gender.data,
            "phone_number": form.phone_number.data,
            "address_1": form.address_1.data,
            "address_2": form.address_2.data,
            "city": form.city.data,
            "state": form.state.data,
            "username": form.username.data,
            "email": form.email.data,
        }
        User.update_user(user_data, user_id)
        flash("Your account information has been updated.", "success")
        return redirect(url_for("base_blueprint.account"))

    elif request.method == "GET":
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.other_name.data = current_user.other_name
        form.gender.data = current_user.gender
        form.address_1.data = current_user.address_1
        form.address_2.data = current_user.address_2
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.postal_code.data = current_user.postal_code
        form.phone_number.data = current_user.phone_number
        form.username.data = current_user.username
        form.email.data = current_user.email
    # get the path for the profile picture of the current user
    profile_picture = f"{s3_url}/{s3_user_img_dir}{current_user.photo}"
    return render_template("account.html", form=form, profile_picture=profile_picture)


@blueprint.route("/logout")
def logout():
    current_user.is_active = False
    logout_user()
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/shutdown")
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."


## Errors


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
