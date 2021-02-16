import json
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)
from app.base.models import Property
from api.schema import property_schema, properties_schema, user_schema
from api.utils.file_handlers import create_images_folder, property_image_handler

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
    return {
        "property": property_schema.dump(prop_data),
        "owner": user_schema.dump(prop_data.prop_owner)
    }


@property_endpoint.route("/api/property/add", methods=["POST"])
@jwt_required
def add_property():
    """
    Creates a new property in the database with data from request body.
    """
    data = request.form
    current_user = get_jwt_identity()
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
        Property.add_property(
            prop_data["name"],
            prop_data["desc"],
            prop_data["price"],
            prop_data["location"],
            folder_to_save_images,
            image_list_to_json,
            prop_data["user_id"],
        )

        return jsonify({"created": property_schema.dump(data)})

    except ValidationError as err:  # Returns an error if a required field is missing
        return jsonify({"error": err.messages})


@property_endpoint.route("/api/property/update/<int:prop_id>", methods=["PUT"])
@jwt_required
def update_property(prop_id):
    """
    Updates the details of the property in the database.
    """
    data = request.form

    prop_to_update = Property.query.get(prop_id)

    if not prop_to_update:
        return jsonify({"message": "Invalid ID"})

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
        Property.update_property(
            prop_id,
            prop_data['name'],
            prop_data['desc'],
            prop_data['price'],
            prop_data['_location'],
            images_folder,
            image_list_to_json,
            prop_data['user_id'])
        return jsonify({"message": "The details of the property has been updated."}), 201
    except ValidationError as err:
        return jsonify(err.messages)
    except KeyError as err:
        return jsonify(err)


@property_endpoint.route("/api/property/delete/<int:prop_id>", methods=["DELETE"])
@jwt_required
def delete_property(prop_id):
    """
    Deletes a property from database by querying using the ID from the request json data.
    """
    if Property.delete_property(prop_id):
        return jsonify({"message": "The property has been deleted"})

    return jsonify({"message": f"Property with ID {prop_id} was not found."})
