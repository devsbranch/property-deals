import jsonschema
from flask import jsonify, json, request, Response
from app import db
from app.base.models import User
from api.schemas.user_schema import add_user_schema
from api.helpers import validate_email, validate_username
from app.base.utils import generate_url_and_email_template


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


def add_user():
    from app.tasks import send_email
    request_data = request.get_json()
    try:
        jsonschema.validate(request_data, add_user_schema)
        if validate_username(request_data["username"]):
            return jsonify({"message": "The username is already taken. Please try a different one."})
        if validate_email(request_data["email"]):
            return jsonify({"message": "The email you entered is already registered. Please try a different one."})

        user = User(**request_data)
        db.session.add(user)
        db.session.commit()

        email_template, subject = generate_url_and_email_template(
            request_data["email"],
            request_data["username"],
            request_data["first_name"],
            request_data["last_name"],
            email_category="verify_email",
        )
        send_email.delay(request_data["email"], subject, email_template)

        response = Response(json.dumps(request_data), 201, mimetype="application/json")
        return response
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        return jsonify({"message": "invalid data"}), 400
