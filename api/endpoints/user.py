import jsonschema
from flask import jsonify, json, request, Response
from app import db
from app.base.models import User
from api.schemas.user_schema import add_user_schema
from api.helpers import validate_email, validate_username


def get_users():
    """
    Returns a json object of all the users int he database.
    """
    response = jsonify({"users": User.get_all_users()})
    return response


def get_user_by_id(user_id):
    user = User.get_user_by_id(user_id)
    if not user:
        return jsonify("User not found"), 404
    return jsonify(user), 200
