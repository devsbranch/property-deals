from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, UserProfileUpdateForm
from app.base.models import User
from app.base.utils import save_image_to_redis
from app.tasks import profile_image_process, delete_profile_image
from config import IMAGE_UPLOAD_CONFIG


aws_s3_bucket_name = IMAGE_UPLOAD_CONFIG["amazon_s3"]["S3_BUCKET"]
s3_image_url = IMAGE_UPLOAD_CONFIG["amazon_s3"]["S3_URL"]
aws_bucket_name = IMAGE_UPLOAD_CONFIG["amazon_s3"]["S3_BUCKET"]
profile_image_upload_dir = IMAGE_UPLOAD_CONFIG["image_save_directories"]["USER_PROFILE_IMAGES"]
cover_image_upload_dir = IMAGE_UPLOAD_CONFIG["image_save_directories"]["USER_COVER_IMAGES"]
image_server_config = IMAGE_UPLOAD_CONFIG["storage_location"]


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

        flash("Your account has been created.", "success")
        return redirect(url_for("base_blueprint.login"))

    return render_template("accounts/register.html", form=form)


@login_required
@blueprint.route("my_profile/<user_id>", methods=["GET", "POST"])
def user_profile(user_id):
    user_to_update = User.query.get_or_404(user_id)
    form = UserProfileUpdateForm(obj=user_to_update)

    if request.method == "POST" and form.validate_on_submit():
        if request.files.get("profile_photo").filename != "":  # Check if a profile image has been uploaded
            # Delete the previous profile image if it exists
            delete_profile_image.delay(profile_image_upload_dir, user_to_update.profile_photo, s3_bucket_name=aws_s3_bucket_name)
            file = request.files.get("profile_photo")
            filename = save_image_to_redis(file)
            profile_image_process.delay(filename, photo_type="profile")
            user_to_update.profile_photo = filename
            user_to_update.prof_photo_loc = image_server_config

        if request.files.get("cover_photo").filename != "":  # Check if a cover image has been uploaded
            # Delete the previous profile image if it exists
            delete_profile_image.delay(cover_image_upload_dir, user_to_update.cover_photo, s3_bucket_name=aws_s3_bucket_name)
            file = request.files.get("cover_photo")
            filename = save_image_to_redis(file)
            profile_image_process.delay(filename, photo_type="cover")
            user_to_update.cover_photo = filename
            user_to_update.cover_photo_loc = image_server_config

        for key, value in request.form.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]
            if key == "password":  # Check if password is in the form
                if value:
                    value = generate_password_hash(value)  # Hash the password from the form
                else:
                    # Maintain the old user's password in the database if password was not in form
                    value = current_user.password
            setattr(user_to_update, key, value)
        db.session.commit()
        flash("Your account information has been updated.", "success")
        return redirect(url_for("base_blueprint.user_profile", user_id=current_user.id))

    elif request.method == "GET":
        # Populates the form fields with user data.
        form.populate_obj(user_to_update)
    return render_template(
        "accounts/settings.html",
        form=form,
        s3_image_url=s3_image_url,
        profile_image_dir=profile_image_upload_dir,
        cover_image_dir=cover_image_upload_dir
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
