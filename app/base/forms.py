import os
from wtforms.fields.html5 import DateField, IntegerField
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.fields import MultipleFileField
from wtforms.validators import Email, DataRequired, ValidationError, Length, EqualTo
from app.base.models import User


# login and registration
class LoginForm(FlaskForm):
    username = StringField("Username", id="username_login", validators=[DataRequired()])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    first_name = StringField(
        "First Name", validators=[DataRequired(), Length(min=2, max=30)]
    )
    last_name = StringField(
        "Last Name", validators=[DataRequired(), Length(min=2, max=30)]
    )
    other_name = StringField("Other Name")
    birth_date = DateField("Birthday", validators=[DataRequired()])
    gender = SelectField(
        "Gender", choices=["Gender", "Male", "Female"], validators=[DataRequired()]
    )
    phone = IntegerField("Phone", validators=[DataRequired()])
    address_1 = StringField(
        "Address Line 1", validators=[DataRequired(), Length(min=2, max=150)]
    )
    address_2 = StringField(
        "Address Line 2", validators=[DataRequired(), Length(min=2, max=100)]
    )
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=30)])
    postal_code = StringField(
        "Postal Code", validators=[DataRequired(), Length(min=2, max=20)]
    )
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField(
        "Your Email", validators=[DataRequired(), Email(), Length(min=2, max=30)]
    )
    password = PasswordField(
        "Your Password", validators=[DataRequired(), Length(min=8, max=60)]
    )
    register = SubmitField("Sign Up")

    def validate_username(self, username):
        """
        Will raise a validation error if the username submitted from the form already exists in the database.
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "The username is already taken. Please try a different one."
            )

    def validate_email(self, email):
        """
        Will raise a validation error if the email submitted from the form already exists in the database
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "The email you entered is already registered. Please try a different one."
            )

    def validate_gender(self, gender):
        """
        Checks if the user has selected gender either Male or Female from the Select Field.
        """
        if gender.data == "Gender":
            raise ValidationError("You need to select your gender.")

    def validate_other_name(self, other_name):
        """
        Check if the user has provided the other name and if the length is within the number of allowed characters.
        If the user hasn't provided input, it will be ignored.
        """
        if 0 < len(other_name.data) < 2:
            raise ValidationError("Field must be between 2 and 30 characters long.")


class RequestResetPasswordForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=5, max=60)]
    )
    submit = SubmitField("Recover Password")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError(
                "The account with the email you have provided doesn't exist."
            )


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            Length(min=6, max=60),
            EqualTo("confirm_password", message="Passwords must be equal"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), Length(min=6, max=60)]
    )
    submit = SubmitField("Reset Password")


class UserProfileUpdateForm(CreateAccountForm):
    username = StringField("Username", validators=[Length(min=2, max=20)])
    email = StringField("Your Email", validators=[Email(), Length(min=2, max=30)])
    password = PasswordField("Your Password")
    profile_photo = FileField(
        "Select profile Photo",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images Only!")],
    )
    cover_photo = FileField(
        "Select cover Photo",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images Only!")],
    )
    save = SubmitField("Save All")

    def validate_username(self, username):
        """
        Will only do these validation checks if the username or email the user enters is
        different than the current_user username and email address.
        """
        if username.data != current_user.username:
            # Will raise a validation errors if the username submitted from the form already exists in the database
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "The username is already taken. Please try a different one."
                )

    def validate_email(self, email):
        """Will raise a validation errors if the email submitted from the form already exists in the database"""
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "The email you entered is already registered. Please try a different one."
                )

    def validate_other_name(self, other_name):
        """
        Check if the user has provided the other name and if the length is within the number of allowed characters.
        If the user hasn't provided input, it will be ignored.
        """
        if 0 < len(other_name.data) < 2:
            raise ValidationError("Field must be between 2 and 30 characters long.")

    def validate_gender(self, gender):
        """
        Checks if the user has selected gender either Male or Female from the Select Field.
        """
        if gender.data == "Gender":
            raise ValidationError("You need to select your gender.")

    def validate_password(self, password):
        """
        Checks if the user has provided the password. If the length of password.data is 0, it means the user hasn't
        provided a password and the form will be submitted and validated without a password input. If the length of the
        password is greater than 1, it means password is provided and the user wants to change the password, then it is
        checked for validation before the form is submitted.
        """
        if 0 < len(password.data) < 8:
            raise ValidationError("Field must be between 8 and 20 characters long.")


class CreatePropertyForm(FlaskForm):
    name = StringField(
        "Property Name", validators=[DataRequired(), Length(min=5, max=50)]
    )
    desc = TextAreaField(
        "Property Description", validators=[DataRequired(), Length(min=10, max=300)]
    )
    type = SelectField(
        "Property For ...",
        choices=[
            "Select",
            "Rent",
            "Sale",
        ],
        validators=[DataRequired()],
    )
    photos = MultipleFileField(
        "Upload photos of your property",
        validators=[
            DataRequired(),
            Length(
                min=1, max=10, message="Upload 1 or more photos and not more that 10"
            ),
        ],
    )
    price = StringField("Price", validators=[DataRequired(), Length(min=1, max=50)])
    location = StringField(
        "Property Location", validators=[DataRequired(), Length(min=2, max=50)]
    )
    submit = SubmitField("Create")

    def validate_prop_photos(self, photos):
        ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
        for file in photos.data:
            if os.path.splitext(file.filename)[1] not in ALLOWED_EXTENSIONS:
                raise ValidationError("Only Images are allowed e.g jpg, jpeg, png")

    def validate_prop_type(self, type):
        """
        Checks if the user has selected gender either Male or Female from the Select Field.
        """
        if type.data == "Select":
            raise ValidationError("You need to select your property listing type.")


class UpdatePropertyForm(CreatePropertyForm):
    photos = MultipleFileField(
        "Upload photos of your property",
    )

    def validate_prop_photos(self, photos):
        ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
        for file in photos.data:
            if os.path.splitext(file.filename)[1] not in ALLOWED_EXTENSIONS:
                raise ValidationError("Only Images are allowed e.g jpg, jpeg, png")

    submit = SubmitField("Update")


class SearchForm(FlaskForm):
    q = StringField("search property", validators=[DataRequired()])
    search = SubmitField("search")

    def __init__(self, *args, **kwargs):
        """
        The __init__ constructor provides values for the form data and csrf_enabled arguments if they are not provided
        by the caller.
        """
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "csrf_token" not in kwargs:
            kwargs["csrf_token"] = False
        super(SearchForm, self).__init__(*args, **kwargs)
