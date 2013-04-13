from .base import *

ALLOWED_HOSTS = ['.herokuapp.com']

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = 'https://s3.amazonaws.com/readraven/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'd97cr2v8mtahbt',
        'USER': 'emsbqjbpbijsgv',
        'PASSWORD': '4V-Dx8cQ_EZs0FZHE2JzYbH4sc',
        'HOST': 'ec2-23-21-161-255.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}
