import pdb
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
    birth_date = db.Column(db.DateTime, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address_1 = db.Column(db.String(200), nullable=False)
    address_2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    profile_photo = db.Column(
        db.String(100), nullable=False, default="assets/img/default.jpg"
    )
    cover_photo = db.Column(
        db.String(100), nullable=False, default="assets/img/default_cover.jpg"
    )
    prof_photo_loc = db.Column(db.String(100), nullable=True)  # specifies the server hosting the image
    cover_photo_loc = db.Column(db.String(100), nullable=True)  # specifies the server hosting the image
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    date_verified = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_property_listings = db.relationship("Property", backref="property_listing_owner", lazy=True)

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
    photos_location = db.Column(db.String(100), nullable=True)  # specifies the server hosting the image
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
        """
        Saves the Property listing data to the database.
        """
        new_property = cls(**prop_data)
        db.session.add(new_property)
        db.session.commit()
        # Add Property listing data to ElasticSearch index
        add_to_index(new_property.id, prop_data["name"], prop_data["desc"], prop_data["location"])

    @classmethod
    def update_property(cls, prop_data, prop_id):
        property_to_update = Property.query.filter_by(id=prop_id)
        for key, value in prop_data.items():
            property_to_update.update({key: value})
            db.session.commit()
        # Update Property listing data in ElasticSearch index
        add_to_index(prop_id, prop_data["name"], prop_data["desc"], prop_data["location"])

    @classmethod
    def update_property_images(cls, image_dir, img_list, prop_id):
        """
        Updates the photos(list of image filenames) and the images folder in the database.
        """
        prop_to_update = Property.query.get(prop_id)
        prop_to_update.image_folder = image_dir
        prop_to_update.photos = img_list
        db.session.commit()

    @classmethod
    def delete_property(cls, prop_id):
        """
        Deletes the Property listing in the database.
        """
        prop_to_delete = cls.query.get(prop_id)
        delete_from_index(prop_to_delete.id)  # Delete property in ElasticSearch index
        db.session.delete(prop_to_delete)
        db.session.commit()


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
