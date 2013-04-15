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
        userfeeditem = bundle.obj.userfeeditem(bundle.request.user)
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
