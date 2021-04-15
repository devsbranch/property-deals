# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
from wtforms.fields.html5 import DateField, IntegerField
from flask import request
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    FileField,
    SelectField,
)
from wtforms.validators import Email, DataRequired, Length, ValidationError, EqualTo
from flask_wtf.file import FileAllowed
from wtforms.fields import MultipleFileField
from flask_login import current_user
from app.base.models import User


# login and registration
class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    birth_date = DateField('Birthday', validators=[DataRequired()])
    gender = SelectField('Gender', choices=["Gender", "Male", "Female"], validators=[DataRequired()])
    phone = IntegerField('Phone', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    zip = StringField('ZIP', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class UpdateAccountForm(CreateAccountForm):
    picture = FileField(
        "Change your profile picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"])],
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


class RequestResetPasswordForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=5, max=60)]
    )
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("The account with the email you have provided doesn't exist.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[Length(min=6, max=60), EqualTo("confirm_password",
                                                                                    message="Passwords must be equal")])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), Length(min=6, max=60)]
    )
    submit = SubmitField("Reset Password")


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
            "Rent",
            "Sale"
        ],
    )
    prop_photos = MultipleFileField(
        "Upload photos of your property",
        validators=[
            DataRequired(),
            Length(
                min=2, max=8, message="Upload 2 or more photos and not more that 15"
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

    def validate_prop_photos(self, prop_photos):
        ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
        for file in prop_photos.data:
            if os.path.splitext(file.filename)[1] not in ALLOWED_EXTENSIONS:
                raise ValidationError("Only Images are allowed e.g jpg, jpeg, png")


class UpdatePropertyForm(CreatePropertyForm):
    prop_photos = MultipleFileField(
        "Upload photos of your property",
    )

    def validate_prop_photos(self, prop_photos):
        if prop_photos.data[0].filename == "":
            return True  # Means the user hasn't updated the images
        ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
        for file in prop_photos.data:
            if os.path.splitext(file.filename)[1] not in ALLOWED_EXTENSIONS:
                raise ValidationError("Only Images are allowed e.g jpg, jpeg, png")

    submit = SubmitField("Update")


class SearchForm(FlaskForm):
    q = StringField("search property", validators=[DataRequired()])
    search = SubmitField("search")

    def __init__(self, *args, **kwargs):
        """
        The __init__ constructor provides values for the formdata and csrf_enabled arguments if they are not provided
        by the caller.
        """
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "csrf_token" not in kwargs:
            kwargs["csrf_token"] = False
        super(SearchForm, self).__init__(*args, **kwargs)
