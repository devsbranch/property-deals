# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import json
from datetime import date
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from app import db
from app.base.forms import CreatePropertyForm, UpdatePropertyForm
from app.base.models import Property
from app.home import blueprint
from config import S3_BUCKET_CONFIG
from app.base.utils import generate_dir_name, resize_images, save_to_redis

bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
image_path = S3_BUCKET_CONFIG["S3_URL"] + "/" + S3_BUCKET_CONFIG["PROP_ASSETS"]
s3_prop_img_dir = S3_BUCKET_CONFIG["PROP_ASSETS"]


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
        image_path=image_path
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


@blueprint.route("/property/create", methods=["GET", "POST"])
@login_required
def create_property():
    form = CreatePropertyForm()

    if form.validate_on_submit():
        img_files = request.files.getlist("prop_photos")
        redis_img_key = save_to_redis(img_files)

        s3_upload_dir = generate_dir_name()
        output_filenames = resize_images(redis_img_key, s3_upload_dir)
        img_list_to_json = json.dumps(output_filenames)

        prop_data = {
            "name": form.prop_name.data,
            "desc": form.prop_desc.data,
            "price": form.prop_price.data,
            "image_folder": output_filenames[0],
            "photos": img_list_to_json,
            "location": form.prop_location.data,
            "type": form.prop_type.data,
            "condition": form.prop_condition.data,
            "user_id": current_user.id,
        }

        Property.add_property(prop_data)
        flash("Your Property has been listed")
        return redirect(url_for("home_blueprint.index"))
    return render_template("create_property.html", form=form)


@blueprint.route("/property/details/<int:property_id>")
def details(property_id):
    prop_data = Property.query.get_or_404(property_id)
    # converts the json object from the db to a python dictionary
    photos = json.loads(prop_data.photos)
    return render_template(
        "property_details.html", prop_data=prop_data, photos_list=photos, image_path=image_path
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
    from app.tasks import delete_img_obj
    prop_to_update = Property.query.get(property_id)

    form = UpdatePropertyForm()
    if request.method == "POST" and form.validate_on_submit():
        if request.files["prop_photos"].filename:
            if request.files["prop_photos"].filename:
                # delete previous images before
                delete_img_obj.delay(
                    bucket,
                    s3_prop_img_dir + prop_to_update.image_folder,
                    json.loads(prop_to_update.photos)
                )

                img_files = request.files.getlist("prop_photos")
                redis_img_keys = save_to_redis(img_files)

                s3_upload_dir = generate_dir_name()
                output_filenames = resize_images(redis_img_keys, s3_upload_dir)
                img_list_to_json = json.dumps(output_filenames)

                prop_to_update.image_folder = output_filenames[0]
                prop_to_update.photos = img_list_to_json
                db.session.commit()

        prop_data = {
            "name": form.prop_name.data,
            "desc": form.prop_desc.data,
            "price": form.prop_price.data,
            "type": form.prop_type.data,
            "condition": form.prop_condition.data,
            "location": form.prop_location.data,
        }
        Property.update_property(prop_data, property_id)
        flash("Your Property listing has been updated", "success")
        return redirect(url_for("home_blueprint.index"))

    elif request.method == "GET":
        prop_to_update = Property.query.get(property_id)
        # prefills the forms with the attributes to the property to be updated
        form.prop_name.data = prop_to_update.name
        form.prop_desc.data = prop_to_update.desc
        form.prop_price.data = prop_to_update.price
        form.prop_location.data = prop_to_update.location
        form.prop_type.data = prop_to_update.type
        form.prop_condition.data = prop_to_update.condition

    return render_template("update_property.html", form=form)


@blueprint.route("/property/delete/<int:prop_id>", methods=["POST"])
@login_required
def delete_property(prop_id):
    Property.delete_property(prop_id)
    return redirect(url_for("home_blueprint.index"))