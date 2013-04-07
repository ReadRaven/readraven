from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from libgreader import GoogleReader, OAuth2Method
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

from raven import settings
from raven.models import CredentialsModel


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
    if not request.user.is_anonymous():
        # XXX: Assumes a Google OAuth2 credential!
        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        credential = storage.get()

        # XXX: Wonder if we should be doing more validation here to see
        # if it is expired or not...
        if credential is None or credential.invalid:
            FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                           request.user)
            authorize_url = FLOW.step1_get_authorize_url()
            return HttpResponseRedirect(authorize_url)

        auth = OAuth2Method(credential.client_id, credential.client_secret)
        auth.authFromAccessToken(credential.access_token)
        auth.setActionToken()

        reader = GoogleReader(auth)
        info = reader.getUserInfo()

        return render_to_response(
            'raven/index.html',
            {'user': info['userName'], 'email': info['userEmail']},
            context_instance=RequestContext(request))
    else:
        return render_to_response(
            'raven/index.html',
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
        user = User.objects.get(username=email[:30])
    except User.DoesNotExist:
        user = User.objects.create_user(email[:30])
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)

    # This fakes the same process as authenticate, but since we're using
    # a mechanism authenticate doesn't support, we'll do this ourselves.
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return HttpResponseRedirect("/")
