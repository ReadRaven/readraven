from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.conf import settings

def index(request):
    return render_to_response(
        'usher/index.html',
        context_instance=RequestContext(request))
