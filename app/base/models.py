# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import Binary, Column, Integer, String

from app import db, login_manager

from app.base.util import hash_pass


# class User(db.Model, UserMixin):
#     __tablename__ = 'User'
#
#     id = Column(Integer, primary_key=True)
#     username = Column(String, unique=True)
#     email = Column(String, unique=True)
#     password = Column(Binary)
#
#     def __init__(self, **kwargs):
#         for property, value in kwargs.items():
#             # depending on whether value is an iterable or not, we must
#             # unpack it's value (when **kwargs is request.form, some values
#             # will be a 1-element list)
#             if hasattr(value, '__iter__') and not isinstance(value, str):
#                 # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
#                 value = value[0]
#
#             if property == 'password':
#                 value = hash_pass(value)  # we need bytes here (not plain str)
#
#             setattr(self, property, value)
#
#     def __repr__(self):
#         return str(self.username)


# @login_manager.user_loader
# def user_loader(id):
#     return User.query.filter_by(id=id).first()
#
#
# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get('username')
#     user = User.query.filter_by(username=username).first()
#     return user if user else None


import json
from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager
from config import S3_BUCKET_CONFIG
# from app.search import add_to_index, delete_from_index, search_docs


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
    is_verified = db.Column(db.Boolean, nullable=True, default=False)
    date_verified = db.Column(db.DateTime, nullable=True)

    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_properties = db.relationship("Property", backref="prop_owner", lazy=True)

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
    def update_user(data, user_id):
        """
        This function will update the user in the database. Here, the .first() function is not called
        on the user_to_update object because we want the object to have the .update() method which we will use
        update the user_to_update object by iterating through the data object and getting a key=value pair.
        """
        user_to_update = User.query.filter_by(id=user_id)
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
    name = db.Column(db.Text, nullable=False)
    desc = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.String, nullable=False)
    location = db.Column(db.Text, nullable=False)
    image_folder = db.Column(
        db.Text, nullable=True
    )  # Do we need this as a db attribute?
    photos = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), default="other", nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    deal_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.ForeignKey("User.id"), nullable=False)
    owner = db.relationship("User")

    @classmethod
    def search_property(cls, search_term, page, per_page):
        """
        This method queries for properties in database matching the ids returned by the search_docs().
        """
        ids, total = search_docs(search_term, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        ids_to_query = []
        for i in range(len(ids)):
            ids_to_query.append((ids[i], i))
        results = cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(ids_to_query, value=cls.id)
        )
        return results, total

    @classmethod
    def add_property(cls, prop_data):
        new_property = cls(**prop_data)
        db.session.add(new_property)
        db.session.commit()
        # Add property to ElasticSearch index
        add_to_index(
            new_property.id, prop_data["name"], prop_data["desc"], prop_data["location"]
        )

    @classmethod
    def update_property(cls, prop_data, prop_id):
        property_to_update = Property.query.filter_by(id=prop_id)
        for key, value in prop_data.items():
            property_to_update.update({key: value})
            db.session.commit()
        add_to_index(
            prop_id, prop_data["name"], prop_data["desc"], prop_data["location"]
        )

    @classmethod
    def update_property_images(cls, image_dir, img_list, prop_id):
        prop_to_update = Property.query.get(prop_id)
        prop_to_update.image_folder = (
            image_dir  # deletes old property image folder including contents
        )
        prop_to_update.photos = img_list
        db.session.commit()

    @classmethod
    def delete_property(cls, prop_id):
        from app.tasks import delete_img_obj

        prop_to_delete = cls.query.get(prop_id)
        bucket = S3_BUCKET_CONFIG["S3_BUCKET"]
        path_to_delete = S3_BUCKET_CONFIG["PROP_ASSETS"] + prop_to_delete.image_folder
        image_list = json.loads(prop_to_delete.photos)

        delete_img_obj.delay(bucket, path_to_delete, image_list)
        delete_from_index(prop_to_delete.id)  # Delete property in ElasticSearch index

        db.session.delete(prop_to_delete)
        db.session.commit()
        return "Done"


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
