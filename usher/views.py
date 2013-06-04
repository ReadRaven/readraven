from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.forms import ModelForm


from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import stripe
from payments.models import Customer
from raven import tasks
from .models import UserTakeoutUpload

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


class UserTakeoutUploadForm(ModelForm):
    class Meta:
        model = UserTakeoutUpload
        fields = ['zipfile']

@login_required
def import_takeout(request):
    if request.method == 'POST':
        i = UserTakeoutUpload(user=request.user)
        form = UserTakeoutUploadForm(request.POST, request.FILES, instance=i)
        if form.is_valid():
            takeout = form.save()

            task = tasks.EatTakeoutTask()
            result = task.delay(request.user, takeout.zipfile.name)

    # This isn't the prettiest, but it works.
    #return HttpResponseRedirect(reverse('usher.views.dashboard'))
    return HttpResponseRedirect('/usher/dashboard#import')

@login_required
def dashboard(request):
    user = request.user
    takeout = user.takeouts
    last_upload = None
    zipfile = None
    for t in takeout.values():
        last_upload = t['upload_date']
        zipfile = t['zipfile'].replace('takeouts/', '')

    return render_to_response(
        'usher/dashboard.html',
        { 'last_upload' : last_upload,
          'zipfile' : zipfile },
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

            # TODO: get to 1.0 so we can start charging for reals!
            customer.subscribe('free', trial_days=14)
        except stripe.StripeError, e:
            # At least one error is known:
            #   Your card was declined. Your request was in test mode, but
            #   used a non test card. For a list of valid test cards,
            #   visit: https://stripe.com/docs/testing
            print "ERROR:", e

        # All good! Goto thankyou?
        return HttpResponseRedirect("/")
    else:
        if request.user.is_customer():
            # Redirect to / in production mode, fall through in DEBUG mode
            if settings.DEBUG is False:
                return HttpResponseRedirect("/")

    task = tasks.SyncFromReaderAPITask()
    result = task.delay(request.user, loadLimit=150)
    request.user.sync_task_id = result.task_id
    request.user.save()

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
