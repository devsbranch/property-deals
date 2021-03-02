from app import celeryapp, db
from app.base.models import User

celery = celeryapp.celery


@celery.task()
def save_user_to_db(data):
    User.add_user(data)
    return "User added"


@celery.task()
def update_user_data(data, username):
    User.update_user(data, username)
    return "User Updated"
