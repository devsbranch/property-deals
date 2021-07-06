from app import ma
from marshmallow import fields


class UserSchema(ma.Schema):
    id = fields.String()
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    other_name = fields.String()
    gender = fields.String(required=True)
    phone = fields.String(required=True)
    profile_photo = fields.String()
    cover_photo = fields.String()
    prof_photo_loc = fields.String()
    cover_photo_loc = fields.String()
    date_registered = fields.DateTime()
    is_verified = fields.Boolean()
    date_verified = fields.DateTime()
    username = fields.String(required=True)
    email = fields.String(required=True)
    acc_deactivated = fields.Boolean()
    date_to_delete_acc = fields.DateTime()


user_schema = UserSchema()
users_schema = UserSchema(many=True)
