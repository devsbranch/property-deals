from flask import Blueprint, jsonify, request
from app import db
from app.base.models import User
from api.schema import user_schema, users_schema

api_blueprint = Blueprint("api_blueprint", __name__)


@api_blueprint.route('/api/user/all')
def get_users():
    """ returns a json object of all the users in the database"""
    users = User.query.all()
    return users_schema.jsonify(users)


@api_blueprint.route('/api/user/<int:user_id>', methods=['GET'])
def get_one_user(user_id):
    """ returns a json object of one user matching the id """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"})
    return user_schema.jsonify(user)


@api_blueprint.route('/api/user', methods=['POST'])
def add_user():
    """ creates new user in the database with data from request body"""
    data = request.get_json()
    if "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "must contain username, email and password"})
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "username already exist"})
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "the email is already registered"})

    new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User has been created"})


@api_blueprint.route('/api/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """ updates username and email of user """
    data = request.get_json()
    if "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"message": "payload must contain username and email"})
    user_to_update = User.query.get(user_id)
    if not user_to_update:
        return jsonify({"message": "the username does not exist"})
    user_to_update.username = data['username']
    user_to_update.email = data['email']
    db.session.commit()
    return jsonify({"message": "username and email has been updated"})


@api_blueprint.route('/api/user', methods=['DELETE'])
def delete_user():
    """ deletes user from database with user_id from url """
    data = request.get_json()
    if "username" not in data:
        return jsonify({"message": "username missing. you need to submit a username to delete"})
    user_to_delete = User.query.filter_by(username=data['username']).first()
    if not user_to_delete:
        return jsonify({"message": "the username does not exist"})
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({"message": "user has been deleted"})