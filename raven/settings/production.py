from .base import *

ALLOWED_HOSTS = ['.herokuapp.com']

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = 'https://s3.amazonaws.com/readraven/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'd8ij5eddp5m7rp',
        'USER': 'fosibpjnqdhrax',
        'PASSWORD': 'wEl_rZsLsVSdrI0pCtmFrdNfVy',
        'HOST': 'ec2-23-21-89-65.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}

