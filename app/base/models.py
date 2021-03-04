# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
import shutil, os
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from app import db, login_manager
from api.schema import property_schema, user_schema
from app.base.file_handler import property_image_handler


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    other_name = db.Column(db.String(30), nullable=True)
    gender = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address_1 = db.Column(db.String(100), nullable=False)
    address_2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    photo = db.Column(
        db.String(100), nullable=True, default="/profile_pictures/default.png"
    )
    is_active = db.Column(db.Boolean, default=False)
    is_vendor = db.Column(db.Boolean, default=False)

    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_properties = db.relationship("Property", backref="prop_owner", lazy=True)

    def to_json(self):
        """
        This function returns a json representation of the object. This is useful if we want to include and
        return data related to the instance from other database tables
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "photo": self.photo,
            "user_properties": [
                property_schema.dump(prop) for prop in self.user_properties
            ],
        }

    @staticmethod
    def get_all_users():
        return [user.to_json() for user in User.query.all()]

    @classmethod
    def get_user(cls, _user_id):
        return cls.query.get(_user_id)

    @classmethod
    def username_exists(cls, _username):
        return bool(cls.query.filter_by(username=_username).first())

    @classmethod
    def email_exists(cls, _email):
        return bool(cls.query.filter_by(email=_email).first())

    @classmethod
    def add_user(cls, data):
        new_user = cls(**data)
        db.session.add(new_user)
        db.session.commit()

    @staticmethod
    def update_user(data, username):
        """
        This function will update the user in the database. Here, the .first() function is not called
        on the user_to_update object because we want the object to have the .update() method which we will use
        update the user_to_update object by iterating through the data object and getting a key=value pair.
        """
        user_to_update = User.query.filter_by(username=username)
        for key, value in data.items():
            user_to_update.update({key: value})
            db.session.commit()

    @staticmethod
    def delete_user(_user_id):
        properties_to_delete = Property.query.filter_by(user_id=_user_id)
        for prop in properties_to_delete:
            db.session.delete(prop)
        is_successful = User.query.filter_by(id=_user_id).delete()
        db.session.commit()
        return bool(is_successful)


class Property(db.Model):

    __tablename__ = "property"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(64), nullable=False)
    desc = db.Column(db.Text(256), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.Text(64), nullable=False)
    image_folder = db.Column(
        db.Text, nullable=True
    )  # Do we need this as a db attribute?
    photos = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), default="other", nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    deal_done = db.Column(db.Boolean, default=False)
    condition = db.Column(db.String(30), default="Used", nullable=False)
    user_id = db.Column(db.ForeignKey("User.id"), nullable=False)
    owner = db.relationship("User")

    def to_json(self):
        """
        This function returns the a json representation of the object. This is useful if we want to include and
        return data related to the instance from other database tables
        """
        return {
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "price": self.price,
            "date": self.date,
            "location": self.location,
            "image_folder": self.image_folder,
            "photos": self.photos,
            "user_id": self.user_id,
            "owner": user_schema.dump(self.prop_owner),
        }

    @staticmethod
    def get_all_properties():
        return [prop.to_json() for prop in Property.query.all()]

    @classmethod
    def get_property(cls, _prop_id):
        query = cls.query.get(_prop_id)
        return property_schema.dump(query)

    @classmethod
    def add_property(
        cls, prop_data
    ):
        new_property = cls(**prop_data)
        db.session.add(new_property)
        db.session.commit()

    @classmethod
    def update_property(cls, prop_data, prop_id):
        property_to_update = Property.query.filter_by(id=prop_id)
        for key, value in prop_data.items():
            property_to_update.update({key: value})
            db.session.commit()

    @classmethod
    def delete_property(cls, prop_id):
        prop_to_delete = cls.query.get(prop_id)
        if prop_to_delete:
            images_folder = os.path.join(
                f"{current_app.root_path}/base/static/{prop_to_delete.image_folder}"
            )
            shutil.rmtree(images_folder)
            db.session.delete(prop_to_delete)
            db.session.commit()
            return True
        return False


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
