from app import celeryapp, create_app
from config import config_dict
from app import get_config_mode

app_config = config_dict[get_config_mode.capitalize()]

app = create_app(app_config)

celery = celeryapp.make_celery(app)
celeryapp.celery = celery
