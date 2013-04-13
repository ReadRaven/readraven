from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SESSION_COOKIE_SECURE = False

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
