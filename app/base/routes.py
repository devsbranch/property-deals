# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import uuid
from flask import render_template, redirect, request, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, UpdateAccountForm
from app.base.models import User
from app.base.utils import save_to_redis
from config import S3_BUCKET_CONFIG

s3_url = S3_BUCKET_CONFIG["S3_URL"]
s3_bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
s3_user_img_dir = S3_BUCKET_CONFIG["USER_ASSETS"]


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/errors-<errors>")
def route_errors(error):
    return render_template("errors/{}.html".format(error))


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


@blueprint.route("/register", methods=["GET", "POST"])
def register():
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
            # delete previous image
            delete_img_obj.delay(s3_bucket, s3_user_img_dir, filename=current_user.photo)

            image = request.files["picture"]
            redis_img_key = save_to_redis([image])
            rand_str = str(uuid.uuid4())[:13].replace("-", "") + ".jpg"
            image_process.delay(redis_img_key[0], s3_user_img_dir, rand_str)
            current_user.photo = rand_str
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
            "postal_code": form.postal_code.data,
            "state": form.state.data,
            "username": form.username.data,
            "email": form.email.data,
        }
        User.update_user(user_data, user_id)
        flash("Your account information has been updated.", "success")
        return redirect(url_for("base_blueprint.account"))

    elif request.method == "GET":
        form.username.data = current_user.username
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
    profile_picture = s3_url + "/" + s3_user_img_dir + current_user.photo
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
