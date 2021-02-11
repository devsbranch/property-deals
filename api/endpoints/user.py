from flask import Blueprint, jsonify, request
from app import db
from app.base.models import User
from api.schema import user_schema, users_schema


user_endpoint = Blueprint("user_blueprint", __name__)


@user_endpoint.route('/api/user/list')
def get_users():
    """
    Returns a json object of all the users in the database.
    """
    users = User.query.all()
    return users_schema.jsonify(users)


@user_endpoint.route('/api/user/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    """
    Returns a json object of one user matching the id.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": f"The user with id {user_id} was not found."})
    return user_schema.jsonify(user)


@user_endpoint.route('/api/user/add', methods=['POST'])
def add_user():
    """
    Creates new user in the database with data from request body.
    """
    data = request.get_json()
    if "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "Must contain username, email and password."})
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "The username already exist."})
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "The email is already registered."})
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": f"The user {data['username']} has been created."})


@user_endpoint.route('/api/user/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Updates username and email of user in the database.
    """
    data = request.get_json()
    if "username" not in data or "email" not in data:
        return jsonify({"message": "Payload must contain username and email."})
    user_to_update = User.query.get(user_id)
    if not user_to_update:
        return jsonify({"message": f"The user with id {user_id} does not exist"})
    user_to_update.username = data['username']
    user_to_update.email = data['email']
    db.session.commit()
    return jsonify({"message": "The username and email has been updated."})


@user_endpoint.route('/api/user/delete/<username>', methods=['DELETE'])
def delete_user(username):
    """
    Deletes user from database with the user id from the url
    """
    data = request.get_json()
    if "username" not in data:
        return jsonify({"message": "The username is missing. You need to submit a username to delete."})
    user_to_delete = User.query.filter_by(username=username).first()
    if not user_to_delete:
        return jsonify({"message": "The username does not exist."})
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({"message": f"The user '{username}' has been deleted."})
