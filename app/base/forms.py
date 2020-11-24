# -*- encoding: utf-8 -*-
"""
Copyright (c) 2020 - DevsBranch
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, MultipleFileField
from wtforms.validators import InputRequired, Email, DataRequired, Length
from flask_wtf.file import FileRequired


## login and registration

class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create', validators=[DataRequired()])
    email = StringField('Email', id='email_create', validators=[DataRequired(), Email()])
    password = PasswordField('Password', id='pwd_create', validators=[DataRequired()])

class CreateListing(FlaskForm):
    property_name = StringField("Property name", id="prop_name", validators=[DataRequired(), Length(min=5, max=50)])
    property_desc = StringField("Property Description", id='prop_desc', validators=[DataRequired(), Length(min=10, max=500)])
    # photos = MultipleFileField("upload photos")
    location = StringField("Location", id='location', validators=[DataRequired(), Length(min=1, max=50)])
    create_listing = SubmitField("Create listing")
