from app import celeryapp, create_app

app = create_app()
celery = celeryapp.make_celery(app)
celeryapp.celery = celery
