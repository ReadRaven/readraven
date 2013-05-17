from django.conf.urls import patterns, include, url

from tastypie.api import Api

from raven import resources


v09 = Api(api_name='0.9')
v09.register(resources.FeedResource())
v09.register(resources.FeedItemResource())

urlpatterns = patterns(
    '',
    url(r'api/', include(v09.urls)),
    url(r'^home', 'raven.views.home'),
    url(r'^values', 'raven.views.values'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^$', 'raven.views.index'),
    url(r'^usher/sign_up', 'usher.views.sign_up'),
    url(r'^usher/sign_in', 'usher.views.sign_in'),
    url(r'^usher/dashboard', 'usher.views.dashboard'),
    url(r'^usher/import_takeout', 'usher.views.import_takeout'),
    url(r'^usher/google_auth', 'usher.views.google_auth'),
    url(r'^google_auth_callback', 'usher.views.google_auth_callback'),
)
