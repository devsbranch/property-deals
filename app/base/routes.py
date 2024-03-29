import datetime
from flask import render_template, redirect, request, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, login_manager
from app.base import blueprint
from app.base.forms import (
    LoginForm,
    CreateAccountForm,
    UserProfileUpdateForm,
    RequestResetPasswordForm,
    ResetPasswordForm,
    ConfirmAccountDeletionForm,
    ReactivateAccountForm,
    SearchForm
)
from app.base.models import User, DeactivatedUserAccounts
from app.base.utils import (
    save_image_to_redis,
    confirm_token,
    generate_url_and_email_template,
)
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


@blueprint.before_request
def before_request():
    """
    This function make the Search form and the global profile_image_dir(used in the navigation.html) GLOBAL,
    accessible in any template without passing it in render_template().
    """
    g.search_form = SearchForm()
    g.profile_image_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["USER_PROFILE_IMAGES"]



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

        email_template, subject = generate_url_and_email_template(
            form.email.data,
            form.username.data,
            form.first_name.data,
            form.last_name.data,
            email_category="verify_email",
        )
        send_email.delay(form.email.data, subject, email_template)
        flash(
            "Your account has been created. Check your inbox to verify your email.",
            "success",
        )
        return redirect(url_for("base_blueprint.login"))

    return render_template("accounts/register.html", form=form)


@blueprint.route("/forgot-password", methods=["GET", "POST"])
def request_password_reset():
    form = RequestResetPasswordForm()

    if current_user.is_authenticated:
        logout_user()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        email_template, subject = generate_url_and_email_template(
            user.email,
            user.username,
            user.first_name,
            user.last_name,
            email_category="password_reset",
        )
        send_email.delay(user.email, subject, email_template)
        flash("An link to reset you password has been sent to your email.", "success")
        return redirect(url_for("home_blueprint.index"))
    return render_template("accounts/forgot_password.html", form=form)


@blueprint.route("/reset-password/<token>", methods=["GET", "POST"])
def password_reset(token):
    form = ResetPasswordForm()

    if current_user.is_authenticated:
        return redirect(url_for("home_blueprint.index"))
    user_data = confirm_token(token)
    if not user_data or user_data["email_category"] != "password_reset":
        flash("The link is invalid or has expired.", "danger")
        return redirect(url_for("home_blueprint.index"))
    user = User.query.filter_by(email=user_data["email"]).first()

    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Your password has been reset", "success")
        return redirect(url_for("base_blueprint.login"))
    return render_template("accounts/reset_password.html", form=form)


@blueprint.route("/verify_email/<token>")
def verify_email(token):
    user_data = confirm_token(token)
    if not user_data or user_data["email_category"] != "verify_email":
        flash("The confirmation email is invalid or has expired")
        return redirect(url_for("home_blueprint.index"))
    user = User.query.filter_by(email=user_data["email"]).first()
    if user.is_verified:
        flash("Your email is already verified")
    else:
        user.is_verified = True
        user.date_verified = datetime.datetime.today()
        db.session.commit()
        flash("Your email has been verified.", "success")
        return redirect(url_for("home_blueprint.index"))


@blueprint.route("/resend")
@login_required
def resend_verification_email():
    email_template, subject = generate_url_and_email_template(
        current_user.email,
        current_user.username,
        current_user.first_name,
        current_user.last_name,
        email_category="verify_email",
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


@blueprint.route("/my-profile", methods=["GET", "POST"])
@login_required
def user_profile():
    form = UserProfileUpdateForm(obj=current_user)
    modal = ConfirmAccountDeletionForm()

    if request.method == "POST" and form.validate_on_submit():
        try:
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

        #  AttributeError: 'NoneType' object has no attribute 'filename'. This error can result from the request not
        #  containing 'profile_photo' and 'cover_photo' stream data in the request body. The error is likely to occur
        #  testing this route with flask.test_client() and not with a browser.
        except AttributeError:
            pass

        flash_message, css_class = (
            "Your account information has been updated.",
            "success",
        )

        for key, value in request.form.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]

            if key == "email":
                # check if user has updated email, then set the is_verified attribute to False so that the user can verify the new email
                if current_user.email != value:
                    setattr(current_user, key, value)
                    current_user.is_verified = False
                    email = value
                    email_template, subject = generate_url_and_email_template(
                        email,
                        current_user.username,
                        current_user.first_name,
                        current_user.last_name,
                        email_category="verify_email",
                    )
                    send_email.delay(value, subject, email_template)
                    flash_message, css_class = (
                        "Your account information has been updated. Check your inbox to verify your new email.",
                        "success",
                    )
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
        flash(flash_message, css_class)
        return redirect(url_for("base_blueprint.user_profile", user_id=current_user.id))

    elif request.method == "GET":
        # Populates the form fields with user data.
        form.populate_obj(current_user)
    return render_template(
        "accounts/settings.html",
        form=form,
        modal=modal,
        s3_image_url=s3_image_url,
        profile_image_dir=profile_image_upload_dir,
        cover_image_dir=cover_image_upload_dir,
    )


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("base_blueprint.login"))


@blueprint.route("/deactivate-account", methods=["GET", "POST"])
@login_required
def account_deletion():
    form = ConfirmAccountDeletionForm()

    if request.method == "POST" and form.validate_on_submit():
        if check_password_hash(current_user.password, form.password.data):
            current_user.acc_deactivated = True
            date_today = datetime.datetime.today()
            date_to_delete_acc = date_today + datetime.timedelta(days=14)
            current_user.date_to_delete_acc = date_to_delete_acc

            # Information of the user account to delete
            account_to_delete = DeactivatedUserAccounts(
                email=current_user.email,
                username=current_user.username,
                date_deactivated=date_today,
                date_to_delete_acc=date_to_delete_acc,
            )

            db.session.add(account_to_delete)
            db.session.commit()

            return redirect(url_for("base_blueprint.deactivated_acc_page"))
        else:
            flash("The password you entered is incorrect.", "danger")
            return redirect(url_for("base_blueprint.user_profile"))
    return redirect(url_for("base_blueprint.user_profile"))


@blueprint.route("/deactivated")
@login_required
def deactivated_acc_page():
    date_of_acc_deletion = current_user.date_to_delete_acc
    if date_of_acc_deletion is None or date_of_acc_deletion.strftime("%d/%m/%y") == "01/01/01":
        return render_template("errors/403.html"), 403
    logout_user()
    return render_template(
        "accounts/account_deactivated.html",
        title="Account Deactivated",
        date_of_acc_deletion=date_of_acc_deletion,
    )


@blueprint.route("/reactivate-account", methods=["GET", "POST"])
def reactivate_account():
    form = ReactivateAccountForm()

    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user_to_reactivate = User.query.filter_by(email=email).first()

        # Check the password
        if user_to_reactivate and check_password_hash(
            user_to_reactivate.password, password
        ):
            if not user_to_reactivate.acc_deactivated:
                flash("Your account is already active.", "warning")
                return redirect(url_for("home_blueprint.index"))
            user_to_reactivate.acc_deactivated = False
            # set to a lowest date. Any date lower than the current date is fine to prevent the celery task from
            # deleting the account should the date match with the current date.
            user_to_reactivate.date_to_delete_acc = datetime.datetime(1, 1, 1, 0, 0, 0)

            # Remove the user account from the DeactivatedUserAccounts after account reactivation
            db.session.delete(
                DeactivatedUserAccounts.query.filter_by(
                    email=user_to_reactivate.email
                ).first()
            )
            db.session.commit()
            login_user(user_to_reactivate)

            flash("Your account has been activated. Welcome back!", "success")
            return redirect(url_for("home_blueprint.index"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("accounts/reactivate_account.html", form=form)


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
