# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    FileField,
)
from wtforms.validators import (
    Email,
    DataRequired,
    Length,
    ValidationError,
)
from flask_wtf.file import FileAllowed
from wtforms.fields import MultipleFileField
from flask_login import current_user
from app.base.models import User


## login and registration
class LoginForm(FlaskForm):
    username = StringField("Username", id="username_login", validators=[DataRequired()])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField(
        "Username", id="username_create", validators=[DataRequired()]
    )
    email = StringField(
        "Email", id="email_create", validators=[DataRequired(), Email()]
    )
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])


class UpdateAccountForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=5, max=40)]
    )
    picture = FileField(
        "Update your profile picture", validators=[FileAllowed(["jpg", "jpeg", "png"])]
    )
    submit = SubmitField("Update")

    def validate_username(self, username):
        """
        Will only do these validation checks if the username or email the user enters is
        different than the current_user username and email address.
        """
        if username.data != current_user.username:
            """ Will raise a validation error if the username submitted from the form already exists in the database """
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "The username is already taken. Please try a different one."
                )

    def validate_email(self, email):
        """ Will raise a validation error if the email submitted from the form already exists in the database """
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "The email you entered is already registered. Please try a different one."
                )


class PropertyForm(FlaskForm):
    prop_name = StringField(
        "Property Name", validators=[DataRequired(), Length(min=5, max=50)]
    )
    prop_desc = TextAreaField(
        "Property Description", validators=[DataRequired(), Length(min=10, max=300)]
    )
    prop_photos = MultipleFileField(
        "Upload photos of your property",
        validators=[
            DataRequired(),
            FileAllowed(["jpeg", "jpg", "png"]),
            Length(
                min=3, max=15, message="Upload 3 or more photos and not more that 15"
            ),
        ],
    )
    prop_price = StringField(
        "Price (ZMW)", validators=[DataRequired(), Length(min=1, max=10)]
    )
    prop_location = StringField(
        "Property location", validators=[DataRequired(), Length(min=5, max=50)]
    )
    submit = SubmitField("Sale Property")
