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
    IntegerField,
    SelectField,
)
from wtforms.validators import Email, DataRequired, Length, ValidationError, EqualTo
from flask_wtf.file import FileAllowed
from wtforms.fields import MultipleFileField
from flask_login import current_user
from app.base.models import User


# login and registration
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class CreateAccountForm(FlaskForm):
    first_name = StringField(
        "First name", validators=[DataRequired(), Length(min=2, max=20)]
    )
    last_name = StringField(
        "Last Name", validators=[DataRequired(), Length(min=2, max=20)]
    )
    other_name = StringField("Other Name", validators=[Length(min=2, max=30)])
    gender = SelectField("Gender", choices=["Select Gender", "Male", "Female"])
    address_1 = StringField(
        "Address 1", validators=[DataRequired(), Length(min=5, max=100)]
    )
    address_2 = StringField(
        "Address 2", validators=[DataRequired(), Length(min=5, max=100)]
    )
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=30)])
    state = StringField("State/Province", validators=[Length(min=0, max=30)])
    postal_code = StringField(
        "Postal Code", validators=[DataRequired(), Length(min=2, max=30)]
    )
    phone_number = IntegerField("Phone Number", validators=[])
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=5, max=60)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=60)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), Length(min=6, max=60), EqualTo("confirm_password")],
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        """ Will raise a validation error if the username submitted from the form already exists in the database """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "The username is already taken. Please try a different one."
            )

    def validate_email(self, email):
        """ Will raise a validation error if the email submitted from the form already exists in the database """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "The email you entered is already registered. Please try a different one."
            )


class UpdateAccountForm(CreateAccountForm):
    picture = FileField(
        "Change your profile picture",
        validators=[FileAllowed(["iso", "jpg", "jpeg", "png"])],
    )
    password = PasswordField("Password", validators=[Length(min=0, max=60)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[Length(min=0, max=60), EqualTo("confirm_password")],
    )
    submit = SubmitField("Update")

    def validate_username(self, username):
        """
        Will only do these validation checks if the username or email the user enters is
        different than the current_user username and email address.
        """
        if username.data != current_user.username:
            """
            Will raise a validation errors if the username submitted from the form already exists in the database
            """
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "The username is already taken. Please try a different one."
                )

    def validate_email(self, email):
        """ Will raise a validation errors if the email submitted from the form already exists in the database """
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "The email you entered is already registered. Please try a different one."
                )


class CreatePropertyForm(FlaskForm):
    prop_name = StringField(
        "Property Name", validators=[DataRequired(), Length(min=5, max=50)]
    )
    prop_desc = TextAreaField(
        "Property Description", validators=[DataRequired(), Length(min=10, max=300)]
    )
    prop_type = SelectField(
        "Property type",
        choices=[
            "Select Category",
            "Electronics",
            "Fashion",
            "Car and Auto Parts",
            "Real Estate",
        ],
    )
    prop_condition = SelectField(
        "Condition",
        choices=["Select Condition", "Used", "Refurbished"],
        validators=[DataRequired()],
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
    submit = SubmitField("Create")


class UpdatePropertyForm(CreatePropertyForm):
    prop_photos = MultipleFileField(
        "Upload photos of your property",
        validators=[FileAllowed(["jpeg", "jpg", "png"])],
    )
    submit = SubmitField("Update")
