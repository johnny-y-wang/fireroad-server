import os
import re
import django

os.environ['DJANGO_SETTINGS_MODULE'] = "fireroad.settings"
django.setup()

from courseupdater.views import *
from requirements.models import *
from django.db import DatabaseError, transaction
from django import db
from fireroad.settings import CATALOG_BASE_DIR

REQUIREMENTS_INFO_KEY = "r_delta"

def update_db():
    RequirementsList.objects.all().delete()

    req_urls = compute_semester_delta(list_semesters()[-1].split('-'), 0, 0)
    for path_name in req_urls[REQUIREMENTS_INFO_KEY]:
        new_req = RequirementsList.objects.create(list_id=os.path.basename(path_name))
        with open(os.path.join(CATALOG_BASE_DIR, path_name), 'rb') as file:
            new_req.parse(file.read().decode('utf-8'))
        new_req.save()

    print("The database was successfully updated with {} requirements files.".format(len(req_urls[REQUIREMENTS_INFO_KEY])))

if __name__ == '__main__':
    update_db()