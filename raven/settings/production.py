from .base import *

# RabbitMQ/Celery settings
import djcelery
djcelery.setup_loader()
BROKER_URL = os.environ.get('CLOUDAMQP_URL', '')
# Only set to 1 for staging/free heroku
#BROKER_POOL = 1

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = 'https://s3.amazonaws.com/readraven/static/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_STORAGE_BUCKET_NAME = 'readraven'

GOOGLE_API_SECRETS = os.path.join(SECRETS_DIR, 'production_client_secrets.json')
GOOGLE_OAUTH2_CALLBACK = 'https://www.readraven.com/google_auth_callback'
