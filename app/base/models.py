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

    def to_json(self):
        """
        This function returns the a json representation of the object. This is useful if we want to include and
        return data related to the instance from other database tables
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'profile_image': self.profile_image,
            'properties_by_user': [property_schema.dump(prop) for prop in self.user_prop]
        }

    @staticmethod
    def get_all_users():
        return [User.to_json(user) for user in User.query.all()]

    @staticmethod
    def get_user(_user_id):
        query = User.query.get(_user_id)
        return query

    @staticmethod
    def username_exists(_username):
        return bool(User.query.filter_by(username=_username).first())

    @staticmethod
    def email_exists(_email):
        return bool(User.query.filter_by(email=_email).first())

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
    owner = db.relationship('User')

    def to_son(self):
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
            "owner": user_schema.dump(self.prop_owner)
        }

    @staticmethod
    def get_all_properties():
        return [Property.to_son(prop) for prop in Property.query.all()]

    @staticmethod
    def get_property(_prop_id):
        query = Property.query.get(_prop_id)
        return property_schema.dump(query)

    @staticmethod
    def add_property(_name, _desc, _price, _location, _image_folder, _photos, _user_id):
        new_property = Property(
            name=_name,
            desc=_desc,
            price=_price,
            location=_location,
            image_folder=_image_folder,
            photos=_photos,
            user_id=_user_id
        )
        db.session.add(new_property)
        db.session.commit()

    @staticmethod
    def update_property(prop_id, _name, _desc, _price, _location, _image_folder, _photos, _user_id):
        prop_ro_update = Property.query.get(prop_id)
        prop_ro_update.name = _name,
        prop_ro_update.desc = _desc,
        prop_ro_update.price = _price,
        prop_ro_update.location = _location,
        prop_ro_update.image_folder = _image_folder,
        prop_ro_update.photos = _photos,
        prop_ro_update.user_id = _user_id
        db.session.commit()

    @staticmethod
    def delete_property(prop_id):
        prop_to_delete = Property.query.get(prop_id)
        if prop_to_delete:
            images_folder = os.path.join(f"{current_app.root_path}/base/static/{prop_to_delete.image_folder}")
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
