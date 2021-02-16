# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import os
import shutil
import random
import string
import json
from datetime import datetime
from flask import render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from app import db
from app.base.forms import PropertyForm, UpdateAccountForm
from app.base.models import Property
from app.home import blueprint
from app.base.image_handler import property_image_handler, save_profile_picture


def create_img_folder(username):
    """
    Generates a random string which will be used as a folder name for storing image files
    of properties uploaded by user.
    """
    s = string.ascii_letters
    output_str = "".join(random.choice(s) for i in range(10))
    property_img_folder = f"property_images/{username}-property{output_str}"
    os.mkdir(f"{current_app.root_path}/base/static/{property_img_folder}")
    return property_img_folder


@blueprint.route("/index")
@login_required
def index():
    properties = Property.query.order_by(Property.date.desc())
    photos = [json.loads(p.photos) for p in properties]

    return render_template(
        "index.html", segment="index", properties=properties, photos_list=photos
    )


@blueprint.route("/<template>")
@login_required
def route_template(template):
    try:

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)

    except TemplateNotFound:
        return render_template("page-404.html"), 404


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


@blueprint.route("/create-property", methods=["GET", "POST"])
@login_required
def create_property():
    form = PropertyForm()
    if form.validate_on_submit():
        img_files = request.files.getlist("prop_photos")
        imgs_folder = create_img_folder(current_user.username)

        image_list = [imgs_folder]
        property_image_handler(img_files, image_list, imgs_folder)
        # convert the python dictionary(img_files) to json string
        image_list_to_json = json.dumps(image_list)

        prop_info = Property(
            name=form.prop_name.data,
            desc=form.prop_desc.data,
            price=form.prop_price.data,
            location=form.prop_location.data,
            image_folder=imgs_folder,
            photos=image_list_to_json,
            user_id=current_user.id,
        )

        db.session.add(prop_info)
        db.session.commit()
        flash("Your Property has been listed")
        return redirect(url_for("home_blueprint.view_properties"))
    return render_template("create_property.html", form=form)


@blueprint.route("/view_properties", methods=["GET", "POST"])
def view_properties():
    properties = Property.query.order_by(Property.date.desc())
    # converts the json object from the db to a python dictionary
    photos = [json.loads(p.photos) for p in properties]

    return render_template(
        "properties.html",
        properties=properties,
        photos_list=photos,
        title="Properties on sale",
    )


@blueprint.route("/property/<int:property_id>")
def details(property_id):
    prop_data = Property.query.get_or_404(property_id)
    # converts the json object from the db to a python dictionary
    photos = json.loads(prop_data.photos)
    return render_template(
        "property_details.html", prop_data=prop_data, photos_list=photos
    )


@blueprint.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            filename = save_profile_picture(form.picture.data)
            current_user.profile_image = filename

        current_user.username = form.username.data
        current_user.email = form.email.data
        flash("Your account information has been updated.", "success")

        db.session.commit()
        return redirect(url_for("home_blueprint.account"))

    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    # get the path for the profile picture of the current user
    profile_picture = url_for("static", filename=f"{current_user.profile_image}")

    property_by_user = Property.query.filter_by(user_id=current_user.id).order_by(
        Property.date.desc()
    )
    photos = [json.loads(p.photos) for p in property_by_user]

    return render_template(
        "account.html",
        form=form,
        property_by_user=property_by_user,
        profile_picture=profile_picture,
        photos_list=photos,
    )


@blueprint.route("/update_property/<int:property_id>", methods=["GET", "POST"])
@login_required
def update_property(property_id):
    prop_to_update = Property.query.get_or_404(property_id)
    form = PropertyForm()

    if request.method == "POST" and form.validate_on_submit():
        img_files = request.files.getlist("prop_photos")
        imgs_folder = prop_to_update.image_folder
        image_list = [
            imgs_folder
        ]  # images folder is added to the list and will used to form a filepath to images

        property_image_handler(img_files, image_list, imgs_folder)
        image_list_to_json = json.dumps(image_list)

        prop_to_update.name = form.prop_name.data
        prop_to_update.desc = form.prop_desc.data
        prop_to_update.price = form.prop_price.data
        prop_to_update.photos = image_list_to_json
        prop_to_update.location = form.prop_location.data
        prop_to_update.date = datetime.utcnow()
        db.session.commit()
        flash("Your Property listing has been updated", "success")
        return redirect(url_for("home_blueprint.view_properties"))

    elif request.method == "GET":
        # prefills the forms with the attributes to the property to be updated
        form.prop_name.data = prop_to_update.name
        form.prop_desc.data = prop_to_update.desc
        form.prop_price.data = prop_to_update.price
        form.prop_location.data = prop_to_update.location

    return render_template("create_property.html", form=form)


@blueprint.route("/delete_property/<int:property_id>", methods=["POST"])
@login_required
def delete_property(property_id):
    prop_to_delete = Property.query.get_or_404(property_id)
    image_dir = os.path.join(
        f"{current_app.root_path}/base/static/{prop_to_delete.image_folder}"
    )
    # delete the specified directory(image_dir) including it's contents from the file system
    shutil.rmtree(image_dir)
    db.session.delete(prop_to_delete)
    db.session.commit()
    return redirect(url_for("home_blueprint.view_properties"))
