from datetime import datetime
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from app import db
from app.base.models import Property
from api.schema import property_schema, properties_schema

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
def add_property():
    """
    Creates a new property in the database with data from request body.
    """
    data = request.get_json()
    try:
        prop_data = property_schema.load(data)
        prop_to_add = Property(
            name=prop_data["name"],
            desc=prop_data["desc"],
            price=prop_data["price"],
            location=prop_data["location"],
            photos=prop_data["photos"],
            user_id=prop_data["user_id"],
        )
        db.session.add(prop_to_add)
        db.session.commit()
        return jsonify({"message": f"The property '{data['name']}' has been created."})

    except ValidationError as err:
        return jsonify({"ERROR": err.messages})


@property_endpoint.route("/api/property/update/<int:prop_id>", methods=["PUT"])
def update_property(prop_id):
    """
    Updates the details of the property in the database.
    """
    data = request.get_json()
    prop_to_update = Property.query.get(prop_id)
    if not prop_to_update:
        return jsonify({"error": f"The property with ID {prop_id} does not exist"})
    try:
        prop_data = property_schema.load(data)
        prop_to_update.name = prop_data["name"]
        prop_to_update.desc = prop_data["desc"]
        prop_to_update.price = prop_data["price"]
        prop_to_update.location = prop_data["location"]
        prop_to_update.photos = prop_data["photos"]
        prop_to_update.date = datetime.utcnow()
        prop_to_update.user_id = prop_data["user_id"]
        db.session.commit()
        return jsonify({"message": "The details of the property has been updated."})
    except ValidationError as err:
        return jsonify(err.messages)


@property_endpoint.route("/api/property/delete/<prop_id>", methods=["DELETE"])
def delete_property(prop_id):
    """
    Deletes a property from database by querying using the ID from the url.
    """
    prop_to_delete = Property.query.get(prop_id)
    if not prop_to_delete:
        return jsonify({"error": f"The property of ID {prop_id} does not exist."})
    db.session.delete(prop_to_delete)
    db.session.commit()
    return jsonify(
        {"message": f"The property listing '{prop_to_delete.name}' has been deleted."}
    )

"""
{
    "access token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTMzMTA3MjAsIm5iZiI6MTYxMzMxMDcyMCwianRpIjoiMWFhN2QwMDItODQ2OS00ZGM2LWFiOGEtNzM3NzZhMGU3OWEyIiwiZXhwIjoxNjEzMzExMDIwLCJpZGVudGl0eSI6ImRhbiIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.jmJGR_Fo7JMyGCWmJOKmxqvoiqLQhPdq0Zept0OyXco",
    "message": "User dan was created",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTMzMTA3MjAsIm5iZiI6MTYxMzMxMDcyMCwianRpIjoiZDBhNWYyMjgtNjEwYS00Mjc5LWJmNGUtNjBjZDI2MzkwMTZmIiwiZXhwIjoxNjE1OTAyNzIwLCJpZGVudGl0eSI6ImRhbiIsInR5cGUiOiJyZWZyZXNoIn0.sdSlWolMJ81VgA79BCH2CFVoZzwhXaSFwrUDr3TB91g"
}

eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTMzMTExNTMsIm5iZiI6MTYxMzMxMTE1MywianRpIjoiMjYwNWZkMGYtYzljNi00NDE3LTkzMTUtYzM3MTQxMTU1OGE2IiwiZXhwIjoxNjEzMzExNDUzLCJpZGVudGl0eSI6ImRhbiIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.b9IlQAiBbDZ-K6VSmyu1jVOk0SYJMN2BJkRkLlTwSkQ
"""