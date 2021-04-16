from wtforms.fields.html5 import DateField, IntegerField
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
)
from wtforms.validators import Email, DataRequired, ValidationError, Length
from app.base.models import User


# login and registration
class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=30)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=30)])
    other_name = StringField('Other Name')
    birth_date = DateField('Birthday', validators=[DataRequired()])
    gender = SelectField('Gender', choices=["Gender", "Male", "Female"], validators=[DataRequired()])
    phone = IntegerField('Phone', validators=[DataRequired()])
    address_1 = StringField('Address Line 1', validators=[DataRequired(), Length(min=2, max=150)])
    address_2 = StringField('Address Line 2', validators=[DataRequired(), Length(min=2, max=100)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=30)])
    postal_code = StringField('ZIP', validators=[DataRequired(), Length(min=2, max=20)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Your Email', validators=[DataRequired(), Email(), Length(min=2, max=30)])
    password = PasswordField('Your Password', validators=[DataRequired(), Length(min=8, max=60)])
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
