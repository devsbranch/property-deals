# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField,SubmitField, FileField
from wtforms.validators import InputRequired, Email, DataRequired,Length
from flask_wtf.file import FileAllowed
from wtforms.fields import MultipleFileField


## login and registration
class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create', validators=[DataRequired()])
    email = StringField('Email', id='email_create', validators=[DataRequired(), Email()])
    password = PasswordField('Password', id='pwd_create', validators=[DataRequired()])


class ListPropertyForm(FlaskForm):
    prop_name = StringField('Property Name', validators=[DataRequired()])
    prop_desc = TextAreaField('Property Description', validators=[DataRequired(), Length(min=10, max=256)])
    prop_photos = MultipleFileField('Upload photos of your property', validators=[FileAllowed(['jpg', 'png'])])
    prop_price = StringField('Price (ZMW)', validators=[DataRequired(), Length(min=1, max=10)])
    prop_location = StringField('Property location', validators=[DataRequired(), Length(min=1, max=64)])
    submit = SubmitField('Sale Property')