from celery import Celery

celery = None
CELERY_TASK_LIST = [
    "app.tasks",
]


def make_celery(app):
    celery = Celery(app.import_name, include=CELERY_TASK_LIST)
    celery.conf.update(app.config)
    celery.conf.update(
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/0",
        timezone="UTC",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
