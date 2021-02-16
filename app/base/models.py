# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import json
from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    profile_image = db.Column(
        db.String(64), nullable=True, default="/profile_pictures/default.png"
    )
    user_prop = db.relationship("Property", backref="prop_owner", lazy=True)

    def json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile_image": self.profile_image,
        }

    @staticmethod
    def get_all_users():
        return [User.json(user) for user in User.query.all()]

    @staticmethod
    def get_user(_user_id):
        query = User.query.get(_user_id)
        return query

    @staticmethod
    def username_exists(_username):
        return_value = User.query.filter_by(username=_username).first()
        return bool(return_value)

    @staticmethod
    def email_exists(_email):
        return_value = User.query.filter_by(email=_email).first()
        return bool(return_value)

    @staticmethod
    def add_user(_username, _email, _password):
        new_user = User(username=_username, email=_email, password=_password)
        db.session.add(new_user)
        db.session.commit()

    @staticmethod
    def update_user(_username, _email, _password, _profile_image):
        user_to_update = User(
            username=_username,
            email=_email,
            password=_password,
            profile_image=_profile_image
        )
        db.session.add(user_to_update)
        db.session.commit()

    @staticmethod
    def delete_user(_user_id):
        properties_to_delete = Property.query.filter_by(user_id=_user_id)
        for prop in properties_to_delete:
            db.session.delete(prop)
        is_successful = User.query.filter_by(id=_user_id).delete()
        db.session.commit()
        return bool(is_successful)

    def __repr__(self):
        user_object = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile_image": self.profile_image
        }
        return json.dumps(user_object)


class Property(db.Model):

    __tablename__ = "property"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(64), nullable=False)
    desc = db.Column(db.Text(256), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.Text(64), nullable=False)
    image_folder = db.Column(db.Text, nullable=True)
    photos = db.Column(db.Text)
    user_id = db.Column(db.ForeignKey("User.id"), nullable=False)
    users = db.relationship(User)

    # def __init__(self, name, desc, price, location, image_folder, photos, user_id):
    #     self.name = name
    #     self.desc = desc
    #     self.price = price
    #     self.location = location
    #     self.photos = photos
    #     self.image_folder = image_folder
    #     self.user_id = user_id
    #
    # @property
    # def serialize(self):
    #     return {
    #         "name": self.name,
    #         "desc": self.desc,
    #         "price": self.price,
    #         "location": self.location,
    #         "photos": self.photos,
    #         "user_id": self.user_id
    #     }


class TokenBlacklist(db.Model):
    """
    This table will store tokens that are revoked
    """
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    return user if user else None
