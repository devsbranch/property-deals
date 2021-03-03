from app import make_celery, create_app, get_config_mode
from config import config_dict

app_config = config_dict[get_config_mode.capitalize()]

celery = make_celery(create_app(app_config))
