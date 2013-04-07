import os

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect

from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

from libgreader import GoogleReader, OAuth2Method

from raven import settings


CLIENT_SECRETS = './raven/purloined/client_secrets.json'
OAUTH2_STORAGE = './raven/purloined/oauth2.dat'
SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.google.com/reader/api/',
    ]

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope=SCOPE,
    redirect_uri='http://localhost:8000/oauth2callback')


#@login_required
def index(request):
    #storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    storage = Storage(OAUTH2_STORAGE)
    credential = storage.get()
    if credential is None or credential.invalid == True:
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       request.user)
        authorize_url = FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)
    else:
        auth = OAuth2Method(credential.client_id, credential.client_secret)
        auth.authFromAccessToken(credential.access_token)
        auth.setActionToken()

        reader = GoogleReader(auth)
        info = reader.getUserInfo()

        html = "Hello %s! Your email is %s." % (info['userName'], info['userEmail'])

        return HttpResponse(html)

#@login_required
def auth_return(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY,
                                   request.REQUEST['state'],
                                   request.user):
        return HttpResponseBadRequest()

    credential = FLOW.step2_exchange(request.REQUEST)
    #storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    storage = Storage(OAUTH2_STORAGE)
    storage.put(credential)
    return HttpResponseRedirect("/")

