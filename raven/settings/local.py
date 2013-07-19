from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ()

# RabbitMQ/Celery settings
import djcelery
djcelery.setup_loader()
BROKER_URL = 'amqp://readraven:readraven@localhost:5672/readraven'

# Use this for testing celery tasks
TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

DEFAULT_FILE_STORAGE = 'storages.backends.overwrite.OverwriteStorage'

GOOGLE_API_SECRETS = os.path.join(SECRETS_DIR, 'local_client_secrets.json')
GOOGLE_OAUTH2_CALLBACK = 'http://localhost:8000/google_auth_callback'
