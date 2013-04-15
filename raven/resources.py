import json

from django.core.exceptions import ObjectDoesNotExist
from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.resources import ModelResource

from raven import models


class FeedResource(ModelResource):
    '''A resource representing Feeds.'''
    class Meta:
        allowed_methods = ('get',)
        authentication = SessionAuthentication()
        default_format = 'application/json'
        fields = ['description', 'title', 'link']
        queryset = models.Feed.objects.all()
        resource_name = 'feed'

    def get_object_list(self, request):
        return models.Feed.objects.for_user(request.user)

    def obj_get(self, bundle=None, **kwargs):
        bundle.obj = models.Feed.objects.get(pk=kwargs['pk'])
        bundle.obj.userfeed(bundle.request.user)
        return bundle.obj


class UserFeedResource(ModelResource):
    '''A resource representing UserFeeds (subscriptions).'''
    link = fields.CharField(attribute='link', null=True)

    class Meta:
        #allowed_methods = ('delete', 'post',)
        authentication = SessionAuthentication()
        default_format = 'application/json'
        fields = ['link', ]
        queryset = models.UserFeed.objects.all()
        resource_name = 'subscription'

    def obj_create(self, bundle=None, **kwargs):
        data = json.loads(bundle.request.body)
        try:
            feed = models.Feed.objects.get(link=data['link'])
        except ObjectDoesNotExist:
            feed = models.Feed(link=data['link'])
            feed.save()
        feed.add_subscriber(bundle.request.user)
        return

    def obj_delete(self, bundle=None, **kwargs):
        raise

    def obj_delete_list(self, bundle=None, **kwargs):
        data = json.loads(bundle.request.body)
        feed = models.Feed.objects.get(link=data['link'])
        userfeed = feed.userfeed(bundle.request.user)
        userfeed.delete()


class FeedItemResource(ModelResource):
    '''A resource representing FeedItems.'''
    class Meta:
        allowed_methods = ('get', 'put',)
        authentication = SessionAuthentication()
        default_format = 'application/json'
        fields = ['description', 'link', 'published', 'title']
        queryset = models.FeedItem.objects.all()
        resource_name = 'item'

    feed = fields.ForeignKey(FeedResource, 'feed')
    read = fields.BooleanField()

    def get_object_list(self, request):
        return models.FeedItem.objects.for_user(request.user)

    def obj_get(self, bundle=None, request=None, **kwargs):
        bundle.obj = models.FeedItem.objects.get(pk=kwargs['pk'])
        bundle.obj.userfeeditem(bundle.request.user)
        return bundle.obj

    def obj_update(self, bundle, request=None, **kwargs):
        bundle.obj = models.FeedItem.objects.get(pk=kwargs['pk'])
        userfeeditem = bundle.obj.userfeeditem(bundle.request.user)
        userfeeditem.read = bundle.data['read']
        userfeeditem.save()
        return bundle

    def dehydrate_read(self, bundle):
        userfeeditem = bundle.obj.userfeeditem(bundle.request.user)
        return userfeeditem.read
