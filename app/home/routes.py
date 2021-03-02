# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import os
import shutil
import json
from pathlib import Path
from datetime import date
from datetime import datetime
from flask import render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from app import db
from app.base.forms import PropertyForm
from app.base.models import Property
from app.home import blueprint
from app.base.file_handler import (
    property_image_handler,
    create_images_folder,
)

ALLOWED_IMG_EXT = [".png", ".jpg", ".jpeg"]


@blueprint.route("/index")
def index():
    page = request.args.get("page", 1, type=int)
    property_photos = Property.query.order_by(Property.date.desc())
    photos = [json.loads(p.photos) for p in property_photos]
    paginate_properties = Property.query.paginate(page=page, per_page=10)
    today = date.today()
    return render_template(
        "index.html",
        segment="index",
        properties=paginate_properties,
        photos_list=photos,
        today=today,
    )


@blueprint.route("/<template>")
def route_template(template):
    try:

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)

    except TemplateNotFound:
        return render_template("404.html"), 404


# Helper - Extract current page name from request
def get_segment(request):
    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


def read_dir_imgs(img_dir):
    """
    Gets a directory name and recursively reads images and validates them before saving to list.
    """
    path = f"{current_app.root_path}/base/static/{img_dir}"
    image_list = [img_dir]
    for img in os.listdir(path):
        if Path(img).suffix in ALLOWED_IMG_EXT:
            image_list.append(img)
        continue
    return image_list


@blueprint.route("/property/create", methods=["GET", "POST"])
@login_required
def create_property():
    from app import tasks
    form = PropertyForm()
    if form.validate_on_submit():
        img_files = request.files.getlist("prop_photos")
        imgs_folder = create_images_folder(current_user.username)

        property_image_handler(current_user.username, img_files, imgs_folder)

        img_list = read_dir_imgs(imgs_folder)
        img_list_to_json = json.dumps(img_list)

        prop_data = {
            "name": form.prop_name.data,
            "desc": form.prop_desc.data,
            "price": form.prop_price.data,
            "location": form.prop_location.data,
            "image_folder": imgs_folder,
            "photos": img_list_to_json,
            "type": form.prop_type.data,
            "condition": form.prop_condition.data,
            "user_id": current_user.id,
        }

        tasks.save_property_data.delay(prop_data)
        flash("Your Property has been listed")
        return redirect(url_for("home_blueprint.index"))
    return render_template("create_property.html", form=form)


@blueprint.route("/property/details/<int:property_id>")
def details(property_id):
    prop_data = Property.query.get_or_404(property_id)
    # converts the json object from the db to a python dictionary
    photos = json.loads(prop_data.photos)
    return render_template(
        "property_details.html", prop_data=prop_data, photos_list=photos
    )


@blueprint.route("/my-listings/<int:user_id>")
@login_required
def user_listing(user_id):
    user_listings = Property.query.filter_by(user_id=user_id)
    photos = [json.loads(p.photos) for p in user_listings]
    return render_template(
        "my_properties.html", properties=user_listings, photos_list=photos
    )


@blueprint.route("/property/update/<int:property_id>", methods=["GET", "POST"])
@login_required
def update_property(property_id):
    prop_to_update = Property.query.get_or_404(property_id)
    form = PropertyForm()

    if request.method == "POST" and form.validate_on_submit():
        img_files = request.files.getlist("prop_photos")
        imgs_folder = prop_to_update.image_folder

        img_list = read_dir_imgs(imgs_folder)
        property_image_handler(current_user.username, img_files, imgs_folder)
        image_list_to_json = json.dumps(img_list)

        prop_to_update.name = form.prop_name.data
        prop_to_update.desc = form.prop_desc.data
        prop_to_update.price = form.prop_price.data
        prop_to_update.photos = image_list_to_json
        prop_to_update.location = form.prop_location.data
        prop_to_update.date = datetime.utcnow()
        db.session.commit()
        flash("Your Property listing has been updated", "success")
        return redirect(url_for("home_blueprint.index"))

    elif request.method == "GET":
        # prefills the forms with the attributes to the property to be updated
        form.prop_name.data = prop_to_update.name
        form.prop_desc.data = prop_to_update.desc
        form.prop_price.data = prop_to_update.price
        form.prop_location.data = prop_to_update.location

    return render_template("create_property.html", form=form)


@blueprint.route("/property/delete/<int:property_id>", methods=["POST"])
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
    return redirect(url_for("home_blueprint.index"))
