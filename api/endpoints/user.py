from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required,
    get_raw_jwt
)
from app import db
from app.base.models import User
from api.utils import token_utils
from api.schema import user_schema, property_schema, add_user_schema
from api.utils.file_handlers import save_profile_picture
from api.utils.token_utils import save_revoked_token

user_endpoint = Blueprint("user_blueprint", __name__)


@user_endpoint.route("/api/user/login", methods=["POST"])
def login_user():
    """
    This function will login/authenticate the user by generating an access token and
    a refresh token for the login credentials.
    """
    data = request.get_json()
    if "username" not in data or "password" not in data:
        return jsonify({"message": "You need to provide a username and password"})
    username = data["username"]
    password = data["password"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return "user not found"
    if not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password"})

    return token_utils.generate_access_token(user.username)


@user_endpoint.route("/api/user/logout/access", methods=["POST"])
@jwt_required
def logout_access():
    """
    This function will logout the user, revoke the token and save the revoked
    token to the database.
    """
    jti = get_raw_jwt()["jti"]
    try:
        # Revoking access token
        save_revoked_token(jti)
        return jsonify({"message": "Access token has been revoked"})
    except AttributeError:
        return {"message": "Something went wrong"}, 500


@user_endpoint.route("/api/user/list")
@jwt_required
def get_users():
    """
    Returns a json object of all the users in the database.
    """
    users = User.get_all_users()
    return jsonify(users)


@user_endpoint.route("/api/user/<id>", methods=["GET"])
@jwt_required
def get_one_user(id):
    """
    Returns a json object of one user matching the id.
    """

    user = User.get_user(id)
    try:
        props_of_user = [property_schema.dump(prop) for prop in user.user_prop]
    except AttributeError:
        return jsonify({"message": f"The user with id {id} was not found."})
    return {
        "user": {
            "user_data": user_schema.dump(user),
            "properties_by_user": props_of_user
        }
    }


@user_endpoint.route("/api/user/register", methods=["POST"])
def register_user():
    """
    Creates new user in the database and generate an access token and a refresh token
    from request data.
    """
    data = request.get_json()
    try:
        verified_data = add_user_schema.load(data)
        if User.username_exists(verified_data['username']):
            return jsonify({"message": "Username already exist"})
        elif User.email_exists(verified_data['email']):
            return jsonify({"message": "Email already exist"})
        password = generate_password_hash(verified_data["password"])
        User.add_user(
            verified_data["username"],
            verified_data["email"],
            password
        )
        return jsonify({
            "new_user": [
                data,
                token_utils.generate_access_token(data['username'])
            ]
        })
    except ValidationError as err:
        return jsonify(err.messages)


@user_endpoint.route("/api/user/update/<int:id>", methods=["PUT"])
@jwt_required
def update_user(id):
    """
    Updates username and email of user in the database.
    """
    user_to_update = User.get_user(id)
    data = request.form
    try:
        verified_data = add_user_schema.load(data)
        username = verified_data["username"]
        email = verified_data["email"]
        password = verified_data["password"]
        photo = request.files["photo"]

        if photo.filename == "":
            return jsonify({"message": "You need to upload a profile picture"}), 401

        user_to_update.username = username
        user_to_update.email = email
        user_to_update.password = generate_password_hash(password)
        user_to_update.profile_image = save_profile_picture(username, photo)
        db.session.commit()
        return jsonify({"updated_user": data})
    except ValidationError as err:
        return jsonify({"message": err.messages})


@user_endpoint.route("/api/user/delete/<int:id>", methods=["DELETE"])
@jwt_required
def delete_user(id):
    """
    Deletes user from database with the user id from the url
    """
    jti = get_raw_jwt()["jti"]
    if User.delete_user(id):  # Then delete properties of user as well.
        save_revoked_token(jti)
        return jsonify({"message": "User has been deleted"})
    else:
        return jsonify({"message": "user not found"})