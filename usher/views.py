from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext

from django import forms


from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import stripe
from payments.models import Customer
from raven import tasks

User = get_user_model()

CLIENT_SECRETS = settings.GOOGLE_API_SECRETS
SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.google.com/reader/api/',
]

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope=SCOPE,
    redirect_uri=settings.GOOGLE_OAUTH2_CALLBACK)


class UploadFileForm(forms.Form):
    zipfile = forms.FileField()

@login_required
def import_takeout(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['zipfile']
            z = '/tmp/' + str(f)
            with open(z, 'wb+') as dest:
                # XXX: we need to defend against huge file upload attack
                for chunk in f.chunks():
                    dest.write(chunk)

            task = tasks.ImportOPMLTask()
            result = task.delay(request.user, z)

    return HttpResponseRedirect(reverse('usher.views.dashboard'))

@login_required
def dashboard(request):
    return render_to_response(
        'usher/dashboard.html',
        context_instance=RequestContext(request))

def sign_in(request):
    page = request.GET.get('next', '')
    if page == '/usher/sign_up':
        return render_to_response(
            'usher/auth_new_user.html',
            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/usher/google_auth')

@login_required
def sign_up(request):
    if request.method == 'POST':
        try:
            try:
                customer = request.user.customer
            except ObjectDoesNotExist:
                customer = Customer.create(request.user)
            customer.update_card(request.POST.get("stripeToken"))

            # Free trial until 7/4/2013
            free_until = datetime(2013, 7, 4)
            now = datetime.utcnow()
            trial = free_until - now
            if trial.days < 14:
                trial.days = 14
            customer.subscribe('monthly', trial_days=trial.days)
        except stripe.StripeError:
            # hmm... not sure.
            print "ERROR"

        # All good! Goto thankyou?
        return HttpResponseRedirect("/")
    else:
        if request.user.is_customer():
            return HttpResponseRedirect("/")

    task = tasks.SyncFromReaderAPITask()
    result = task.delay(request.user, loadLimit=150)
    request.user.sync_task_id = result.task_id
    request.user.save()

    whitelist = set([
        'alex@chizang.net',
        'alex@readraven.com',
        'paul@eventuallyanyway.com',
        'garrytan@gmail.com',
        'vyduna@gmail.com',
        'jacklevy@gmail.com',
        'lenchiang@gmail.com',
        'vicchiang@gmail.com',
        'bwbovee@gmail.com',
        'lindsayvail@gmail.com',
        'joe.ferrari@gmail.com',])

    if request.user.email not in whitelist:
        return render_to_response(
            'usher/not_yet.html',
            context_instance=RequestContext(request))
    else:
        return render_to_response(
            'usher/sign_up.html',
            context_instance=RequestContext(request))


def google_auth(request):
    FLOW.params['state'] = xsrfutil.generate_token(
        settings.SECRET_KEY, request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)


def google_auth_callback(request):
    if not xsrfutil.validate_token(settings.SECRET_KEY,
                                   request.REQUEST['state'],
                                   request.user):
        return HttpResponseBadRequest()

    try:
        credential = FLOW.step2_exchange(request.REQUEST)
    except FlowExchangeError:
        return HttpResponseRedirect(reverse('raven.views.values'))

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

    return HttpResponseRedirect("/usher/sign_up")
