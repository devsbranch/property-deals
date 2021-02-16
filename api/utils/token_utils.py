from datetime import datetime, timezone
from flask_jwt_extended import (
    create_access_token
)
from app import db, jwt
from app.base.models import TokenBlacklist


def generate_access_token(username):
    """
    This function will generate an access token and from the
    user registration or login details.
    """
    access_token = create_access_token(identity=username)
    return {"message": f"Access token generated", "access token": access_token}


def save_revoked_token(jti):
    """
    This function will revoke the token and save the revoked
    token to the database.
    """
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlacklist(jti=jti, created_at=now))
    db.session.commit()


@jwt.token_in_blacklist_loader
def check_if_token_revoked(jwt_payload):
    """
    This is a callback function to check if a jwt exists in the database blacklist. If it does
    then the jwt has been revoked and can't be used. The protected endpoint will return a
    "Token has been revoked" as a response.
    """
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlacklist.id).filter_by(jti=jti).scalar()
    return token is not None


