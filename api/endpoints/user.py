import pdb
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
)
from app import db
from app.base.models import User, RevokedTokenModel
from api.token_generator import generate_access_token
from api.schema import user_schema, users_schema
from app.base.image_handler import save_profile_picture, property_image_handler

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
    print('query user')
    user = User.query.filter_by(username=username).first()
    print('checking user')
    if not user:
        return 'user not found'
    print('check password')
    if not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password"})

    return generate_access_token(user.username)


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
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.save_revoked_token()
        return {"message": "Access token has been revoked"}
    except AttributeError:
        return {"message": "Something went wrong"}, 500


@user_endpoint.route("/api/user/logout/refresh", methods=["POST"])
@jwt_refresh_token_required
def login_refresh():
    """
    User Logout Refresh Api
    """
    jti = get_raw_jwt()["jti"]
    try:
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.save_revoked_token()
        return {"message": "Refresh token has been revoked"}
    except AttributeError:
        return {"message": "Something went wrong"}, 500


@user_endpoint.route("/api/token/refresh", methods=["POST"])
@jwt_refresh_token_required
def refresh_token():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({"access token": access_token})


@user_endpoint.route("/api/user/list")
def get_users():
    """
    Returns a json object of all the users in the database.
    """
    users = User.query.all()
    return users_schema.jsonify(users)


@user_endpoint.route("/api/user/<id>", methods=["GET"])
def get_one_user(id):
    """
    Returns a json object of one user matching the id.
    """
    user = User.query.get(id)
    if not user:
        return jsonify({"message": f"The user with id {id} was not found."})
    return user_schema.jsonify(user)


@user_endpoint.route("/api/user/register", methods=["POST"])
def register_user():
    """
    Creates new user in the database and generate an access token and a refresh token
    from request data.
    """
    data = request.get_json()
    # Checking if user already exist

    if "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Must contain username, email and password."})
    user = User.query.filter_by(username=data["username"]).first()
    if user:
        return jsonify({"message": f"The username {user.username} already exists"})
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "The email already exists"})

    password = generate_password_hash(data["password"])
    new_user = User(
        username=data["username"],
        email=data["email"],
        password=password
    )
    db.session.add(new_user)
    db.session.commit()
    return generate_access_token(new_user.username)


@user_endpoint.route("/api/user/update", methods=["PUT"])
@jwt_required
def update_user():
    """
    Updates username and email of user in the database.
    """
    data = request.form
    try:
        username = data["username"]
        email = data["email"]
        password = data["password"]
        photo = request.files["photo"]
    except KeyError:
        return jsonify({"error": "KeyError exception occurred"})

    if "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Must contain username, email and password."})
    elif photo.filename == "":
        return jsonify({"message": "You need to upload a profile picture"}), 401

    current_user = get_jwt_identity()
    user_to_update = User.query.filter_by(username=current_user).first()
    if not user_to_update:
        return jsonify({"message": f"The user {current_user} does not exist or you may need a new token"})
    user_to_update.username = username
    user_to_update.email = email
    user_to_update.password = generate_password_hash(password)
    user_to_update.profile_image = save_profile_picture(photo)
    db.session.commit()
    return jsonify({"message": f"The user {username} has been updated."})


@user_endpoint.route("/api/user/delete", methods=["DELETE"])
@jwt_required
def delete_user():
    """
    Deletes user from database with the user id from the url
    """
    jti = get_raw_jwt()["jti"]

    data = request.get_json()
    if "password" not in data:
        return jsonify(
            {
                "message": "The password is missing. You need to provide a password to delete your account."
            }
        )
    current_user = get_jwt_identity()
    user_to_delete = User.query.filter_by(username=current_user).first()

    try:
        if not check_password_hash(user_to_delete.password, data["password"]):
            return jsonify({"message": "Wrong password."})

        db.session.delete(user_to_delete)
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.save_revoked_token()
        db.session.commit()
        return jsonify(
            {
                "message": f"The user '{current_user}' has been deleted and your token has been revoked."
            }
        )
    except AttributeError:
        return jsonify({"message": "User not found"})
