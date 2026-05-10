import sys, os

sys.path.append(os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()