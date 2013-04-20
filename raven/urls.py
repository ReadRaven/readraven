from django.conf.urls import patterns, include, url

from tastypie.api import Api

from raven import resources


v09 = Api(api_name='0.9')
v09.register(resources.FeedResource())
v09.register(resources.FeedItemResource())
v09.register(resources.UserFeedResource())

urlpatterns = patterns(
    '',
    url(r'api/', include(v09.urls)),
    url(r'^google_auth_callback', 'raven.views.google_auth_callback'),
    url(r'^home', 'raven.views.home'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^usher', 'usher.views.index'),
    url(r'^$', 'raven.views.index'),
)
