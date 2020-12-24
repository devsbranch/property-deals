# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from app import db, login_manager

from app.base.util import hash_pass


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.Binary)
    profile_image = db.Column(db.String(64), nullable=True, default='default_profile_img.png')
    user_prop = db.relationship('Property', backref='prop_owner', lazy=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


class Property(db.Model):

    __tablename__ = 'property_listing'

    id = db.Column(db.Integer, primary_key=True)
    property_name = db.Column(db.Text(64), nullable=False)
    property_desc = db.Column(db.Text(256), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    property_price = db.Column(db.Integer, nullable=False)
    property_location = db.Column(db.Text(64), nullable=False)
    user_id = db.Column(db.ForeignKey('User.id'), nullable=False)
    users = db.relationship(User)


class PropertyImage(db.Model):
    
    __tablename__ = 'property_image'
    
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(64), nullable=False)
    property_id = db.Column(db.ForeignKey('property_listing.id'), nullable=False)  # specifies which property the image belongs to.
    property = db.relationship(Property)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
