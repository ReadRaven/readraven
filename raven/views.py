from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect

from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

from libgreader import GoogleReader, OAuth2Method

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
    redirect_uri='http://localhost:8000/oauth2callback')


# XXX: I have no idea if this is the right way to do things.
def usher(request):
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)


def index(request):
    if not request.user.is_anonymous():
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

        html = "Hello %s! Your email is %s." % (info['userName'], info['userEmail'])
        html += "<br><br>"
        html += "<a href=/logout>logout</a>"

        return HttpResponse(html)
    else:
        html = "Hello anonymous user. Wouldn't you like to login?"
        html += "<br><br>"
        html += "<a href=/usher>usher</a>"
        return HttpResponse(html)


def auth_return(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY,
                                   request.REQUEST['state'],
                                   request.user):
        return HttpResponseBadRequest()

    credential = FLOW.step2_exchange(request.REQUEST)
    email = credential.id_token['email']
    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        user = User.objects.create_user(email)

    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)

    # XXX: is this hacky? no idea. internet is hard.
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return HttpResponseRedirect("/")
