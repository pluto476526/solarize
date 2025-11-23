## analytics/utils.py
## pkibuka@milky-way.space

from django.conf import settings
import logging
import json
import os

logger = logging.getLogger(__name__)

def load_CEC_modules():
    path = os.path.join(settings.BASE_DIR, "config", "cec_modules.json")

    with open(path, mode="r") as f:
        modules = json.load(f)
        return modules


def load_CEC_inverters():
    path = os.path.join(settings.BASE_DIR, "config", "cec_inverters.json")

    with open(path, mode="r") as f:
        inverters = json.load(f)
        return inverters

