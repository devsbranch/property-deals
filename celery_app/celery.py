from celery import Celery

# broker='redis://localhost:6379/0',
#                     backend='db+sqlite:///results.sqlite',
#                     include=['celery_app.tasks']

celery_app = Celery('celery_app')

celery_beat_schedule = {
    "call-every-10": {
        "task": "celery_app.tasks.calculate",
        "schedule": 4,
        "args": (3,),
    }
}
# Optional configuration, see the application user guide.
celery_app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="db+sqlite:///results.sqlite",
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule=celery_beat_schedule,
    include=['celery_app.tasks']
)

if __name__ == '__main__':
    celery_app.start()
