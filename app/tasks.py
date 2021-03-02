from app import celeryapp
from app.base.models import User, Property

celery = celeryapp.celery


@celery.task()
def save_user_to_db(data):
    User.add_user(data)
    return "User added"


@celery.task()
def update_user_data(data, username):
    User.update_user(data, username)
    return "User Updated"


@celery.task()
def save_property_data(data):
    Property.add_property(data)
    return "Property Created"


@celery.task()
def update_property_data(data, prop_id):
    Property.update_property(data, prop_id)
    return "Property Updated"
