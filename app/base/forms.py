# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, SelectField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import InputRequired, Email, DataRequired


# login and registration
class LoginForm(FlaskForm):
    username = TextField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    first_name = TextField('First Name', validators=[DataRequired()])
    last_name = TextField('Last Name', validators=[DataRequired()])
    birth_date = DateField('Birthday', validators=[DataRequired()])
    gender = SelectField('Gender', choices=["Gender", "Male", "Female"], validators=[DataRequired()])
    phone = IntegerField('Phone', validators=[DataRequired()])
    address = TextField('Address', validators=[DataRequired()])
    city = TextField('City', validators=[DataRequired()])
    zip = TextField('ZIP', validators=[DataRequired()])
    username = TextField('Username', validators=[DataRequired()])
    email = TextField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
