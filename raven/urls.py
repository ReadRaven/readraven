from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from tastypie.api import Api

from raven import resources


v09 = Api(api_name='0.9')
v09.register(resources.FeedResource09())
v09.register(resources.FeedItemResource09())

v095 = Api(api_name='0.9.5')
v095.register(resources.UserFeedResource())
v095.register(resources.UserFeedItemResource())

urlpatterns = patterns(
    '',
    url(r'api/', include(v09.urls)),
    url(r'api/', include(v095.urls)),

    url(r'^reader/leftside', 'raven.views.leftside', name='reader.leftside'),
    url(r'^reader',
        login_required(TemplateView.as_view(template_name='raven/reader.html')),
        name='raven.reader'),

    url(r'^home', 'raven.views.home'),
    url(r'^values', 'raven.views.values'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    url(r'^$', 'raven.views.index'),
    url(r'^raven/_feedlist', 'raven.views.feedlist'),

    url(r'^usher$', 'usher.views.dashboard'),
    url(r'^usher/$', 'usher.views.dashboard'),
    url(r'^usher/sign_up', 'usher.views.sign_up'),
    url(r'^usher/sign_in', 'usher.views.sign_in'),
    url(r'^usher/dashboard', 'usher.views.dashboard'),
    url(r'^usher/import_takeout', 'usher.views.import_takeout'),
    url(r'^usher/google_auth', 'usher.views.google_auth'),

    url(r'^jssucks', 'raven.views.jssucks'),
    url(r'^google_auth_callback', 'usher.views.google_auth_callback'),
    url(r'^subscriber', include('django_push.subscriber.urls')),
)
