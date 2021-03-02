from app import celeryapp, db
from app.base.models import User

celery = celeryapp.celery


@celery.task()
def save_user_to_db(data):
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return "User added"
