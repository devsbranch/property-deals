from app.base.models import User


def validate_username(username):
    """
    Checks if the username already exists in the database.
    params: username
    type: string
    returns: boolean
    """
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    return False


def validate_email(email):
    """
    Check if the email already exists in the database
    params: email
    type: string
    returns: boolean
    """
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    return False
