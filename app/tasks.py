from app import celeryapp, db
from app.base.models import User
celery = celeryapp.celery


@celery.task()
def save_user_to_db(data):
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return "User added"


# @celery.task()
# def update_user_data(data, user):
#     user = User.query.filter_by(username=user).first()
#     user.first_name = data["first_name"]
#     # user.last_name = data["last_name"],
#     # user.other_name = data["other_name"],
#     # user.gender = data["gender"],
#     # user.phone_number = data["phone_number"],
#     # user.address_1 = data["address_1"],
#     # user.address_2 = data["address_2"],
#     # user.city = data["city"],
#     # user.postal_code = data["postal_code"],
#     # user.state = data["state"],
#     # user.photo = data["photo"],
#     # user.username = data["username"],
#     # user.email = data["email"],
#     # user.password = data["password"]
#     db.session.commit()
