from app import ma
from app.base.models import User, Property


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "profile_image")


user_schema = UserSchema()
users_schema = UserSchema(many=True)
