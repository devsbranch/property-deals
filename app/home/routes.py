# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
from flask import flash, render_template, request, redirect, url_for, g, current_app
from flask_login import current_user
from jinja2 import TemplateNotFound
from flask_login import login_required
from app import redis_client
from app.home import blueprint
from app.base.forms import CreatePropertyForm, UpdatePropertyForm, SearchForm
from app.base.utils import (
    save_property_listing_images_to_redis,
    email_verification_required,
    check_account_status,
)
from app.tasks import process_property_listing_images, delete_property_listing_images
from app.base.models import Property
from config import IMAGE_UPLOAD_CONFIG
profile_image_upload_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "USER_PROFILE_IMAGES"
]
property_listings_images_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"][
    "PROPERTY_LISTING_IMAGES"
]
amazon_s3_url = IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_URL"]


@blueprint.before_request
def before_request():
    """
    This function make the Search form and the global profile_image_dir(used in the navigation.html) GLOBAL,
    accessible in any template without passing it in render_template().
    """
    g.search_form = SearchForm()
    g.profile_image_dir = IMAGE_UPLOAD_CONFIG["IMAGE_SAVE_DIRECTORIES"]["USER_PROFILE_IMAGES"]


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("errors/403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@blueprint.route("/index")
@check_account_status
def index():
    property_listings = Property.query.all()
    property_listing_photos = [json.loads(p.photos) for p in property_listings]
    return render_template(
        "index.html",
        segment="index",
        property_listings=property_listings,
        photos_list=property_listing_photos,
        image_folder=property_listings_images_dir,
        amazon_s3_url=amazon_s3_url
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
@login_required
@email_verification_required
def create_property():
    form = CreatePropertyForm()
    if request.method == "POST" and form.validate_on_submit():
        redis_image_hashmap_key = save_property_listing_images_to_redis(
            request.files.getlist("photos")
        )
        process_property_listing_images.delay(redis_image_hashmap_key)
        image_filenames = redis_client.hgetall(redis_image_hashmap_key)

        list_of_image_filenames = [
            image_name.decode("utf-8") for image_name in image_filenames.keys()
        ]
        # add redis_image_hashmap_key on first index since it is used as a directory name of where to save image files
        list_of_image_filenames.insert(0, f"{redis_image_hashmap_key}/")
        img_list_to_json = json.dumps(list_of_image_filenames)

        prop_data = {
            "name": form.name.data,
            "desc": form.desc.data,
            "price": form.price.data,
            "images_folder": f"{redis_image_hashmap_key}/",
            "photos": img_list_to_json,
            "photos_location": IMAGE_UPLOAD_CONFIG["STORAGE_LOCATION"],
            "location": form.location.data,
            "type": form.type.data,
            "user_id": current_user.id,
        }
        Property.add_property(prop_data)
        flash("Your Property has been listed.", "success")
        return redirect(url_for("home_blueprint.index"))
    return render_template("create_property.html", form=form)


@blueprint.route("/property/details/<int:listing_id>")
@login_required
def listing_details(listing_id):
    property_listing = Property.query.get_or_404(listing_id)
    photos = json.loads(property_listing.photos)
    return render_template(
        "property_details.html",
        property_listing=property_listing,
        photos_list=photos,
        image_folder=property_listings_images_dir,
        amazon_s3_url=amazon_s3_url,
    )


@blueprint.route("/property/update/<int:listing_id>", methods=["GET", "POST"])
@login_required
@email_verification_required
def update_listing(listing_id):

    listing_to_update = Property.query.get_or_404(listing_id)

    if listing_to_update.user_id != current_user.id:
        return render_template("errors/403.html"), 403

    form = UpdatePropertyForm(obj=listing_to_update)
    if request.method == "POST" and form.validate_on_submit():
        try:
            if bool(request.files["photos"]):
                # delete previous images before
                delete_property_listing_images.delay(
                    listing_to_update.photos_location,
                    property_listings_images_dir,
                    listing_to_update.images_folder,
                    json.loads(listing_to_update.photos),
                    IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"],
                )

                redis_image_hashmap_key = save_property_listing_images_to_redis(
                    request.files.getlist("photos")
                )
                process_property_listing_images.delay(redis_image_hashmap_key)
                image_filenames = redis_client.hgetall(redis_image_hashmap_key)

                list_of_image_filenames = [
                    image_name.decode("utf-8") for image_name in image_filenames.keys()
                ]
                # add redis_image_hashmap_key on first index since it is used as a
                # directory name of where to save image files
                list_of_image_filenames.insert(0, f"{redis_image_hashmap_key}/")
                img_list_to_json = json.dumps(list_of_image_filenames)

                Property.update_property_images(
                    listing_to_update, redis_image_hashmap_key, img_list_to_json
                )
        # Catch a key error exception that occurs during testing
        except KeyError:
            pass

        Property.update_property(listing_to_update, request.form)
        flash("Your Property listing has been updated", "success")
        return redirect(url_for("home_blueprint.index"))

    elif request.method == "GET":
        form.populate_obj(listing_to_update)

    return render_template("update_listing.html", form=form)


@blueprint.route("/delete-listing/<int:listing_id>", methods=["GET", "POST"])
@login_required
def delete_listing(listing_id):
    listing_to_delete = Property.query.get_or_404(listing_id)

    if listing_to_delete.user_id == current_user.id:
        delete_property_listing_images.delay(
            listing_to_delete.photos_location,
            property_listings_images_dir,
            listing_to_delete.images_folder,
            json.loads(listing_to_delete.photos),
            IMAGE_UPLOAD_CONFIG["AMAZON_S3"]["S3_BUCKET"],
        )
        Property.delete_property(listing_to_delete)
        flash("Your Property listing has been deleted", "success")
        return redirect(url_for("home_blueprint.index"))
    else:
        return render_template("errors/403.html"), 403


@blueprint.route("/search/")
def search():
    per_page = current_app.config["RESULTS_PER_PAGE"]

    page = request.args.get("page", 1, type=int)
    search_results, total = Property.search_property(
        g.search_form.q.data, page, per_page
    )
    photos = [json.loads(p.photos) for p in search_results]

    next_url = (
        url_for("home_blueprint.search", q=g.search_form.q.data, page=page + 1)
        if total > page * per_page
        else None
    )
    prev_url = (
        url_for("home_blueprint.search", q=g.search_form.q.data, page=page - 1)
        if page > 1
        else None
    )
    return render_template(
        "search.html",
        title="search",
        search_results=search_results,
        total=total,
        image_folder=property_listings_images_dir,
        photos_list=photos,
        amazon_s3_url=amazon_s3_url,
        next_url=next_url,
        prev_url=prev_url,
        search_term=g.search_form.q.data,
    )
