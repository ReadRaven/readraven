from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets

from raven import settings


User = get_user_model()

CLIENT_SECRETS = './raven/purloined/client_secrets.json'
SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.google.com/reader/api/',
]

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope=SCOPE,
    redirect_uri='http://localhost:8000/google_auth_callback')


def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('raven.views.home'))
    return render_to_response(
        'raven/index.html',
        context_instance=RequestContext(request))


@login_required
def home(request):
    return render_to_response(
        'raven/home.html',
        context_instance=RequestContext(request))


def usher(request):
    FLOW.params['state'] = xsrfutil.generate_token(
        settings.SECRET_KEY, request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)


def google_auth_callback(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY,
                                   request.REQUEST['state'],
                                   request.user):
        return HttpResponseBadRequest()

    credential = FLOW.step2_exchange(request.REQUEST)
    email = credential.id_token['email']
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(email, email)

    user.credential = credential
    user.flow = FLOW
    user.save()

    # This fakes the same process as authenticate, but since we're using
    # a mechanism authenticate doesn't support, we'll do this ourselves.
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return HttpResponseRedirect("/")
