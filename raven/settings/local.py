from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SESSION_COOKIE_SECURE = False

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'readraven',
        'USER': 'readraven',
        'PASSWORD': 'readraven',
        'HOST': 'localhost',
        'PORT': '',
    }
}
