web: newrelic-admin run-program gunicorn raven.wsgi
worker: newrelic-admin run-program python manage.py celeryd -E
scheduler: newrelic-admin run-program python manage.py celeryd -E -B
