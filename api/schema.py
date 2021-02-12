from app import ma
from marshmallow import fields, validate

#
# class AddUserValidationSchema(ma.Schema):
#     username = fields.String(validate=validate.Length(min=4, max=20), required=True)
#     email = fields.String(validate=validate.Length(min=5, max=50), required=True)
#     password = fields.String(validate=validate.Length(min=6, max=50), required=True)
#


class UserSchema(ma.Schema):
    id = fields.String()
    username = fields.String(validate=validate.Length(min=5, max=50), required=True)
    email = fields.String(validate=validate.Length(min=10, max=300), required=True)
    profile_image = fields.String(validate=validate.Length(min=1, max=10), required=True)


class PropertySchema(ma.Schema):
    id = fields.String()
    name = fields.String(validate=validate.Length(min=5, max=50), required=True)
    desc = fields.String(validate=validate.Length(min=10, max=300), required=True)
    date = fields.String()
    price = fields.String(validate=validate.Length(min=1, max=10), required=True)
    location = fields.String(validate=validate.Length(min=5, max=50), required=True)
    image_folder = fields.String()
    photos = fields.String()
    user_id = fields.String(required=True)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
property_schema = PropertySchema()
properties_schema = PropertySchema(many=True)
