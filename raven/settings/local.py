from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ()

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

GOOGLE_API_SECRETS = os.path.join(SECRETS_DIR, 'local_client_secrets.json')
GOOGLE_OAUTH2_CALLBACK = 'http://localhost:8000/google_auth_callback'

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
