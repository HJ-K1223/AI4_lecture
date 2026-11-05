import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from config.mount import MountedApplication
application = MountedApplication(get_wsgi_application(), settings.APP_URL_PREFIX)

