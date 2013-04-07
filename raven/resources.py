from tastypie.resources import ModelResource

from raven import models


class FeedResource(ModelResource):
    '''A resource representing Feeds.'''
    class Meta:
        allowed_methods = ('get',)
        fields = ['description', 'title', 'link']
        queryset = models.Feed.objects.all()
        resource_name = 'feed'
