import os
from decouple import config
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from app import db, login_manager
from app.search import add_to_index, delete_from_index, search_docs


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    other_name = db.Column(db.String(30), nullable=True)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    profile_photo = db.Column(
        db.String(100), nullable=False, default=os.environ.get("DEFAULT_PROF_IMG", config("DEFAULT_PROF_IMG"))
    )
    cover_photo = db.Column(
        db.String(100), nullable=False, default=os.environ.get("DEFAULT_COVER_IMG", config("DEFAULT_COVER_IMG"))
    )
    prof_photo_loc = db.Column(
        db.String(100), nullable=True
    )  # specifies the server hosting the image
    cover_photo_loc = db.Column(
        db.String(100), nullable=True
    )  # specifies the server hosting the image
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    date_verified = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    acc_deactivated = db.Column(db.Boolean, nullable=True, default=False)
    date_to_delete_acc = db.Column(db.DateTime, nullable=True)
    password = db.Column(db.String, nullable=False)
    user_property_listings = db.relationship(
        "Property", backref="property_listing_owner", lazy=True
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]
            if key == "password":
                value = generate_password_hash(value)

            setattr(self, key, value)

    def __repr__(self):
        return str(f"User <{self.username}")


class Property(db.Model):
    __tablename__ = "property"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    desc = db.Column(db.Text, nullable=False)
    date_listed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.String, nullable=False)
    location = db.Column(db.Text, nullable=False)
    images_folder = db.Column(db.Text, nullable=True)
    photos = db.Column(db.Text, nullable=False)
    photos_location = db.Column(
        db.String(100), nullable=True
    )  # specifies the server hosting the image
    type = db.Column(db.String(50), default="other", nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    deal_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.ForeignKey("User.id"), nullable=False)
    owner = db.relationship("User")

    def __repr__(self):
        return str(f"Property Listing <{self.name}")

    @classmethod
    def search_property(cls, search_term, page, per_page):
        """
        This method queries for properties in database matching the ids returned by the search_docs().
        """
        ids, total = search_docs(search_term, page, per_page)
        if total == 0 or isinstance(total, dict):
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
        """
        Saves the Property listing data to the database.
        """
        new_property = cls(**prop_data)
        db.session.add(new_property)
        db.session.commit()
        # Add Property listing data to ElasticSearch index
        add_to_index(
            new_property.id, prop_data["name"], prop_data["desc"], prop_data["location"]
        )

    @classmethod
    def update_property(cls, listing, form_data):
        for key, value in form_data.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]
            if key == "photos":
                continue
            setattr(listing, key, value)
        db.session.commit()
        add_to_index(listing.id, listing.name, listing.desc, listing.location)

    @classmethod
    def update_property_images(cls, listing, images_folder, images_list_json):
        """
        Updates the photos(list of image filenames) and the images folder in the database.
        """
        listing.images_folder = f"{images_folder}/"
        listing.photos = images_list_json
        db.session.commit()

    @classmethod
    def delete_property(cls, listing):
        """
        Deletes the Property listing in the database.
        """
        delete_from_index(listing.id)  # Delete property in ElasticSearch index
        db.session.delete(listing)
        db.session.commit()


class DeactivatedUserAccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=True, unique=True)
    username = db.Column(db.String(200), nullable=True, unique=True)
    date_deactivated = db.Column(db.DateTime, nullable=True)
    date_to_delete_acc = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Email: {self.email} Username: {self.username}>"


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
