import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'roshan.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
