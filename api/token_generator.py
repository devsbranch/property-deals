from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)


def generate_access_token(username):
    """
    This function will generate an access token and refresh token from the
    user login details.
    """
    access_token = create_access_token(identity=username)
    return jsonify(
        {
            "message": f"Access token generated",
            "access token": access_token,
        }
    )
