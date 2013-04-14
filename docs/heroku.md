Staging
=======
A staging heroku app has been created using instructions from [1].

	$ heroku create --remote staging
	$ git push staging master

Note that pushing local branches *not* named 'master' results in a nop.
Therefore, we will be more or less required to push our master branch
up to heroku. Which is quite annoying.

Its url is:
	http://readraven-staging.herokuapp.com/

To get it to work properly, at least three environment variables
must be set:

	heroku config:set SECRET_KEY=...
	heroku config:set DJANGO_SETTINGS_MODULE=raven.settings.staging
	heroku config:set HTTPS=on

Also note that the settings in raven/settings/staging.py is quite
important here. Especially note that the database we use there is
different from the production database.

Production
==========
A production heroku app has also been created, but as of this writing,
nothing is really there yet. I expect the only real difference will be
setting the DJANGO_SETTINGS_MODULE=raven.settings.production, but of
course, we shall see.

References
==========
1: https://devcenter.heroku.com/articles/multiple-environments
2: https://devcenter.heroku.com/articles/config-vars
