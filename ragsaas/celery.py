from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ragsaas.settings')

app = Celery('ragsaas')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Set up periodic task
app.conf.beat_schedule = {
    'check-google-drive-every-5-minutes': {
        'task': 'clientadmin.tasks.check_google_drive',
        'schedule': crontab(minute='*/5'),  # Runs every 5 minutes
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
