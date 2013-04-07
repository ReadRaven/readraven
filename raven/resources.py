from tastypie.resources import ModelResource

from raven import models


class FeedResource(ModelResource):
    '''A resource representing Feeds.'''
    class Meta:
        allowed_methods = ('get',)
        fields = ['description', 'title', 'link']
        queryset = models.Feed.objects.all()
        resource_name = 'feed'


class FeedItemResource(ModelResource):
    '''A resource representing FeedItems.'''
    class Meta:
        allowed_methods = ('get',)
        fields = ['description', 'link', 'published', 'title']
        queryset = models.FeedItem.objects.all()
        resource_name = 'item'
