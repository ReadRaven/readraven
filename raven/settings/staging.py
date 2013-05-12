from .base import *

# RabbitMQ/Celery settings
import djcelery
djcelery.setup_loader()
BROKER_URL = os.environ.get('CLOUDAMQP_URL', '')
# Only set to 1 for staging/free heroku
BROKER_POOL = 1

# Use this for testing celery tasks
TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = 'https://s3.amazonaws.com/readraven/static/'

GOOGLE_API_SECRETS = os.path.join(SECRETS_DIR, 'staging_client_secrets.json')
GOOGLE_OAUTH2_CALLBACK = 'https://readraven-staging.herokuapp.com/google_auth_callback'

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
