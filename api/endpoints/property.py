import json, os, shutil
from datetime import datetime
from flask import Blueprint, current_app, jsonify, request
from marshmallow import ValidationError
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
from app import db
from app.base.models import Property, User
from api.schema import property_schema, properties_schema
from api.utils.file_upload_handlers import create_images_folder, property_image_handler


property_endpoint = Blueprint("property_blueprint", __name__)


@property_endpoint.route("/api/property/list")
def get_properties():
    """
    Returns a json object of all the properties in the database.
    """
    properties = Property.query.all()
    return properties_schema.jsonify(properties)


@property_endpoint.route("/api/property/<int:prop_id>", methods=["GET"])
def get_one_property(prop_id):
    """
    Returns a json object of one property matching the ID.
    """
    prop_data = Property.query.get(prop_id)
    if not prop_data:
        return jsonify(
            {"message": f"The property listing with ID {prop_id} was not found."}
        )
    return property_schema.jsonify(prop_data)


@property_endpoint.route("/api/property/add", methods=["POST"])
@jwt_required
def add_property():
    """
    Creates a new property in the database with data from request body.
    """
    data = request.form
    current_user = get_jwt_identity()
    print(current_user)
    if "photos" not in data and request.files["photos"].filename == "":
        return jsonify({"message": "You need to upload photos."})
    try:
        image_files = request.files.getlist("photos")
        folder_to_save_images = create_images_folder(current_user)
        # List of image filenames to save to database
        image_list = property_image_handler(current_user, image_files, folder_to_save_images)

        # convert the python dictionary(image_files) to json string
        image_list_to_json = json.dumps(image_list)
        # Check if the request data matches the schema else raise ValidationError
        prop_data = property_schema.load(data)
        prop_to_add = Property(
            name=prop_data["name"],
            desc=prop_data["desc"],
            price=prop_data["price"],
            location=prop_data["location"],
            image_folder=folder_to_save_images,
            photos=image_list_to_json,
            user_id=prop_data["user_id"],
        )
        db.session.add(prop_to_add)
        db.session.commit()
        return jsonify({"message": f"The property '{data['name']}' has been created."})

    except ValidationError as err:  # Returns an error if a required field is missing
        return jsonify({"error": err.messages})


@property_endpoint.route("/api/property/update", methods=["PUT"])
@jwt_required
def update_property():
    """
    Updates the details of the property in the database.
    """
    data = request.form

    user = get_jwt_identity()  # We get the username from token accessing this URL
    owner = User.query.filter_by(
        username=user
    ).first()  # Then use the username from the token to query a user from db
    prop_to_update = Property.query.get(data["id"])
    if not owner:
        return jsonify({"error": f"User not found"}), 403
    elif not prop_to_update:
        return jsonify({"message": "Invalid ID"})
    elif prop_to_update.user_id != owner.id:
        return jsonify({"message": "Action forbidden"}), 403

    try:
        if "photos" not in data and request.files["photos"].filename == "":
            return jsonify({"message": "You need to upload photos."})
        # Check if the request data matches the schema else raise ValidationError
        prop_data = property_schema.load(data)
        image_files = request.files.getlist("photos")
        images_folder = prop_to_update.image_folder
        # Returns a list containing folder where images are saved and filenames
        image_list = property_image_handler(image_files, images_folder)

        image_list_to_json = json.dumps(image_list)

        prop_to_update.name = prop_data["name"]
        prop_to_update.desc = prop_data["desc"]
        prop_to_update.price = prop_data["price"]
        prop_to_update.location = prop_data["location"]
        prop_to_update.photos = image_list_to_json
        prop_to_update.date = datetime.utcnow()
        prop_to_update.user_id = owner.id
        db.session.commit()
        return (
            jsonify({"message": "The details of the property has been updated."}),
            201,
        )
    except ValidationError as err:
        return jsonify(err.messages)
    except KeyError as err:
        return jsonify(err)


@property_endpoint.route("/api/property/delete", methods=["DELETE"])
@jwt_required
def delete_property():
    """
    Deletes a property from database by querying using the ID from the request json data.
    """
    current_user = get_jwt_identity()
    property_id = request.json["id"]
    owner = User.query.filter_by(username=current_user).first()
    if not owner:
        return jsonify({"message": "User not found"}), 404
    prop_to_delete = Property.query.get(property_id)
    if not prop_to_delete:
        return jsonify({"error": f"Invalid property ID."}), 404

    if prop_to_delete.user_id != owner.id:
        return jsonify({"message": "Action forbidden"}), 403
    images_directory = os.path.join(
        f"{current_app.root_path}/base/static/{prop_to_delete.image_folder}"
    )
    shutil.rmtree(images_directory)
    db.session.delete(prop_to_delete)
    db.session.commit()
    return jsonify(
        {"message": f"The property listing '{prop_to_delete.name}' has been deleted."}
    )
