from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext

from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets

import stripe
from payments.models import Customer


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


def sign_in(request):
    if request.GET['next'] == '/usher/sign_up':
        return render_to_response(
            'usher/auth_new_user.html',
            context_instance=RequestContext(request))
    else:
        return render_to_response(
            'usher/auth_existing_user.html',
            context_instance=RequestContext(request))


@login_required
def sign_up(request):
    if request.method == 'POST':
        try:
            try:
                customer = request.user.customer
            except ObjectDoesNotExist:
                customer = Customer.create(request.user)
            customer.update_card(request.POST.get("stripeToken"))
            customer.subscribe('monthly', trial_days=14)
        except stripe.StripeError:
            # hmm... not sure.
            print "ERROR"

        # All good! Goto thankyou?
        return HttpResponseRedirect("/")
    else:
        if request.user.is_customer():
            return HttpResponseRedirect("/")

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

    return HttpResponseRedirect("/usher/sign_up")