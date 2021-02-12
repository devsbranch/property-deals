import datetime
import jwt
from functools import wraps
from flask import jsonify, request
from decouple import config
from app.base.models import User

SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')


def token_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({"error": "The token is missing"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, 'HS256')
            current_user = User.query.filter_by(username=data['user']).first()
        except:
            return jsonify({"error": "The token is invalid"})
        return function(current_user, *args, **kwargs)
    return decorated_function
