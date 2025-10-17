## data_factory/celery.py
## pkibuka@milky-way.space

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solarize.settings")

app = Celery(
    "solarize",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["data_factory"])

app.conf.beat_schedule = {
    # "fetch-and-save-NASA-data": {
    #     "task": "data_factory.tasks.fetch_nasa_data",
    #     "schedule": 60,
    # },
    # "fetch-CEC-modules": {
    #     "task": "data_factory.tasks.fetch_CEC_modules",
    #     "schedule": 30,
    # },
    "fetch-CEC-inverters": {
        "task": "data_factory.tasks.fetch_CEC_inverters",
        "schedule": 30,
    },
}

