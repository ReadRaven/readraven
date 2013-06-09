import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from raven.models import UserFeed, UserFeedItem

logger = logging.getLogger('django')
User = get_user_model()


def index(request):
    if request.user.is_authenticated() and request.user.is_customer():
        return HttpResponseRedirect(reverse('raven.views.home'))
    return render_to_response(
        'raven/index.html',
        context_instance=RequestContext(request))


def values(request):
    return render_to_response(
        'raven/values.html',
        context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_customer(), login_url='/usher/sign_up')
def home(request):
    return render_to_response(
        'raven/home.html',
        context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_customer(), login_url='/usher/sign_up')
def feedlist(request):
    '''Fragment for the feed list.'''
    tags = UserFeed.userfeed_tags(request.user)
    untagged_feeds = UserFeed.objects.filter(user=request.user).exclude(tags__in=tags).order_by('feed__title')
    context = {
        'tags': tags,
        'untagged_feeds': untagged_feeds
    }
    return render_to_response(
        'raven/feedlist.html', context,
        context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_customer(), login_url='/usher/sign_up')
def leftside(request):
    '''Left side!'''
    unread_count = UserFeedItem.objects.filter(read=False).count()
    tags = UserFeed.userfeed_tags(request.user)
    untagged_feeds = UserFeed.objects.filter(user=request.user).exclude(tags__in=tags).order_by('feed__title')

    untagged_unread_count = 0
    for userfeed in untagged_feeds:
        untagged_unread_count = untagged_unread_count + userfeed.unread_count()

    context = {
        'tags': tags,
        'unread_count': unread_count,
        'untagged_feeds': untagged_feeds,
        'untagged_unread_count': untagged_unread_count
    }
    return render_to_response(
        'raven/leftside.html', context,
        context_instance=RequestContext(request))


@login_required
def jssucks(request):
    if request.method == 'POST':
        logger.error('*** JS Error ***')
        logger.error(' user:\t%s, %s' % (request.user, request.user.pk))
        logger.error(' url:\t%s' % request.POST['location'])
        logger.error(' file:\t%s' % ':'.join((request.POST['file'], request.POST['lineNumber'])))
        logger.error(' error:\t%s' % request.POST['error'])
        logger.error(' ua:\t%s' % request.POST['ua'])
        logger.error('*** JS Error End ***')

    return render_to_response(
        'raven/home.html',
        context_instance=RequestContext(request))
