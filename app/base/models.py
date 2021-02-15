# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

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

    def __repr__(self):
        return str({"username": self.username, "email": self.email})


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

    def __init__(self, name, desc, price, location, photos, user_id):
        self.name = name
        self.desc = desc
        self.price = price
        self.location = location
        self.photos = photos
        self.user_id = user_id

    @property
    def serialize(self):
        return {
            "name": self.name,
            "desc": self.desc,
            "price": self.price,
            "location": self.location,
            "photos": self.photos,
            "user_id": self.user_id
        }


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
