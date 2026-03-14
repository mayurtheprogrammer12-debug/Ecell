import os
import sys

# Add your project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Specify the settings module for your Django project
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Switch to the Django application
from core.wsgi import application
