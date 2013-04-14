from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.resources import ModelResource

from raven import models


class FeedResource(ModelResource):
    '''A resource representing Feeds.'''
    class Meta:
        allowed_methods = ('get',)
        authentication = SessionAuthentication()
        fields = ['description', 'title', 'link']
        queryset = models.Feed.objects.all()
        resource_name = 'feed'


class FeedItemResource(ModelResource):
    '''A resource representing FeedItems.'''
    class Meta:
        allowed_methods = ('get',)
        authentication = SessionAuthentication()
        fields = ['description', 'link', 'published', 'title']
        queryset = models.FeedItem.objects.all()
        resource_name = 'item'

    feed = fields.ForeignKey(FeedResource, 'feed')
    read = fields.BooleanField(default=True)

    def get_object_list(self, request):
        return models.FeedItem.objects.for_user(request.user)

    def dehydrate_read(self, bundle):
        userfeeditem = models.UserFeedItem.objects.get(
            user=bundle.request.user, item=bundle.obj)
        return userfeeditem.read
