from datetime import timedelta

from celery import Celery
from celery.utils.log import get_task_logger
import settings
import client

celery = Celery('tasks', broker=settings.CELERY_BROKER, backend=settings.CELERY_RESULT_BACKEND)

@celery.task
def refresh_plows():
    client.refresh_plows()

client.logger = get_task_logger(__name__)

celery.conf.CELERYBEAT_SCHEDULE = {
    'update-plows': {
        'task': '%s.refresh_plows' % __name__,
        'schedule': timedelta(seconds=30)
    },
}
