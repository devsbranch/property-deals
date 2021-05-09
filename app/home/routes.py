# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
from flask import flash, render_template, request, redirect, url_for
from flask_login import current_user
from jinja2 import TemplateNotFound
from app import redis_client
from app.home import blueprint
from app.base.forms import CreatePropertyForm
from app.base.utils import save_property_listing_images_to_redis
from app.tasks import process_property_listing_images
from app.base.models import Property
from config import IMAGE_UPLOAD_CONFIG


@blueprint.route("/index")
def index():
    return render_template(
        "index.html",
        segment="index"
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
        return render_template("errors/404.html"), 404


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
def create_property():
    form = CreatePropertyForm()

    if request.method == "POST" and form.validate_on_submit():
        redis_image_hashmap_key = save_property_listing_images_to_redis(request.files.getlist("prop_photos"))
        process_property_listing_images.delay(redis_image_hashmap_key)
        image_filenames = redis_client.hgetall(redis_image_hashmap_key)

        list_of_image_filenames = [image_name.decode("utf-8") for image_name in image_filenames.keys()]
        # add redis_image_hashmap_key on first index since it is used as a directory name of where to save image files
        list_of_image_filenames.insert(0, f"{redis_image_hashmap_key}/")
        img_list_to_json = json.dumps(list_of_image_filenames)

        prop_data = {
            "name": form.prop_name.data,
            "desc": form.prop_desc.data,
            "price": form.prop_price.data,
            "images_folder": f"{redis_image_hashmap_key}/",
            "photos": img_list_to_json,
            "photos_location": IMAGE_UPLOAD_CONFIG["STORAGE_LOCATION"],
            "location": form.prop_location.data,
            "type": form.prop_type.data,
            "user_id": current_user.id
        }
        Property.add_property(prop_data)
        flash("Your Property has been listed.", "success")
        return redirect(url_for("home_blueprint.index"))
    return render_template("create_property.html", form=form)
