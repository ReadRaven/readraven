import json

from django.core.exceptions import ObjectDoesNotExist
from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import InvalidSortError
from tastypie.resources import ALL, ALL_WITH_RELATIONS, ModelResource

from raven import models


def _feed_filter(bundle):
    items = bundle.obj.items.filter(
        userfeeditems__in=models.UserFeedItem.objects.filter(
            read=False)).order_by('-published')
    if not len(items):
        items = bundle.obj.items
    return items


class FeedResource09(ModelResource):
    '''A resource representing Feeds.'''
    class Meta:
        allowed_methods = ('get', 'post', 'delete',)
        always_return_data = True
        authentication = SessionAuthentication()
        authorization = Authorization()
        default_format = 'application/json'
        fields = ['description', 'title', 'link', 'id', 'items']
        max_limit = 20
        queryset = models.Feed.objects.all()
        resource_name = 'feed'
    items = fields.ToManyField(
        'raven.resources.FeedItemResource09', _feed_filter)

    def get_object_list(self, request):
        return models.Feed.objects.for_user(request.user).order_by('title')

    def obj_get(self, bundle=None, **kwargs):
        bundle.obj = models.Feed.objects.get(pk=kwargs['pk'])
        bundle.obj.userfeed(bundle.request.user)
        return bundle.obj

    def obj_create(self, bundle=None, **kwargs):
        data = json.loads(bundle.request.body)
        try:
            feed = models.Feed.objects.get(link=data['link'])
        except ObjectDoesNotExist:
            feed = models.Feed(link=data['link'])
            feed.save()
            feed.update()
        feed.add_subscriber(bundle.request.user)

        bundle.obj = feed

        return bundle

    def obj_delete(self, bundle=None, **kwargs):
        try:
            feed = models.Feed.objects.get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            return
        feed.remove_subscriber(bundle.request.user)


class FeedItemResource09(ModelResource):
    '''A resource representing FeedItems.'''
    class Meta:
        allowed_methods = ('get', 'put',)
        always_return_data = True
        authentication = SessionAuthentication()
        authorization = Authorization()
        default_format = 'application/json'
        fields = ['description', 'link', 'published', 'title', 'id']
        filtering = {
            'read': ALL,
            'feed': ALL_WITH_RELATIONS
        }
        max_limit = 20
        queryset = models.FeedItem.objects.all()
        resource_name = 'item'

    feed = fields.ForeignKey(FeedResource09, 'feed', full=True)
    read = fields.BooleanField()

    def get_object_list(self, request):
        #return models.FeedItem.objects.for_user(request.user).order_by(
        #    '-published')
        # TODO: filtering by 'read' really should be an API parameter. For
        # now, however, we're just hardcoding it here.

        userfeeditems = models.UserFeedItem.objects.filter(
            user=request.user,
            read=False)
        return models.FeedItem.objects.filter(
            userfeeditems__in=userfeeditems).order_by('-published')

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


class UserFeedResource(ModelResource):
    '''A resource describing raven.models.UserFeed.'''
    class Meta:
        always_return_data = True
        authentication = SessionAuthentication()
        authorization = Authorization()
        queryset = models.UserFeed.objects.all()
        resource_name = 'feed'
        max_limit = 20

    def build_filters(self, filters=None):
        # This is probably not the right way to do this, but it *seems*
        # performant, and it does what we want.
        orm_filters = super(UserFeedResource, self).build_filters(filters)

        if 'tags' in filters:
            tags = filters['tags'].split(',')
            #queryset = (Q(tags__name__in=[tags]))
            orm_filters.update({'tags': tags})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        # This is probably not the right way to do this, but it *seems*
        # performant, and it does what we want.
        if 'tags' in applicable_filters:
            tags = applicable_filters.pop('tags')
        else:
            tags = None
        semi_filtered = super(UserFeedResource, self).apply_filters(
            request, applicable_filters)
        if tags:
            semi_filtered = semi_filtered.filter(tags__name__in=tags)
        return semi_filtered

    def get_object_list(self, request):
        return super(UserFeedResource, self).get_object_list(request).filter(
            user=request.user.pk)

    def obj_create(self, bundle=None, **kwargs):
        data = json.loads(bundle.request.body)
        link = data['link']
        user = bundle.request.user
        try:
            feed = models.Feed.objects.get(link=link)
        except ObjectDoesNotExist:
            try:
                feed = models.Feed.objects.get(site=link)
            except ObjectDoesNotExist:
                link = models.Feed.autodiscover(link)
                feed = models.Feed(link=link)
                feed.save()
                feed.update()
        feed.add_subscriber(user)

        userfeed = models.UserFeed.objects.get(user=user, feed=feed)
        bundle.obj = userfeed
        return bundle

    def dehydrate(self, bundle):
        bundle.data['description'] = bundle.obj.feed.description
        bundle.data['link'] = bundle.obj.feed.link
        bundle.data['title'] = bundle.obj.feed.title

        bundle.data['tags'] = [tag.name for tag in bundle.obj.tags.all()]
        return bundle


class UserFeedItemResource(ModelResource):
    '''A resource describing raven.models.UserFeedItem.'''
    class Meta:
        authentication = SessionAuthentication()
        authorization = Authorization()
        filtering = {
            'feed': ALL_WITH_RELATIONS,
            'read': ALL,
            'starred': ALL,
        }
        max_limit = 20
        ordering = ('item__published',)
        queryset = models.UserFeedItem.objects.all()
        resource_name = 'item'

    feed = fields.ForeignKey(
        'raven.resources.UserFeedResource', 'feed', readonly=True)

    def build_filters(self, filters=None):
        # This is probably not the right way to do this, but it *seems*
        # performant, and it does what we want.
        orm_filters = super(UserFeedItemResource, self).build_filters(filters)

        # This is a workaround while we sort out the proper fix in the
        # database, which will require more work and thought. We don't want our
        # users to be affected by our reticence.
        if 'feed' in filters:
            userfeed = models.UserFeed.objects.get(pk=filters.get('feed'))
            orm_filters.update({'feed__exact': userfeed.feed.pk})
        if 'tags' in filters:
            tags = filters['tags'].split(',')
            #queryset = (Q(tags__name__in=[tags]))
            orm_filters.update({'tags': tags})
        if 'feed_tags' in filters:
            feed_tags = filters['feed_tags'].split(',')
            #queryset = (Q(tags__name__in=[feed_tags]))
            orm_filters.update({'feed_tags': feed_tags})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        # This is probably not the right way to do this, but it *seems*
        # performant, and it does what we want.
        if 'tags' in applicable_filters:
            tags = applicable_filters.pop('tags')
        else:
            tags = None
        if 'feed_tags' in applicable_filters:
            feed_tags = applicable_filters.pop('feed_tags')
        else:
            feed_tags = None
        semi_filtered = super(UserFeedItemResource, self).apply_filters(
            request, applicable_filters)
        if tags:
            semi_filtered = semi_filtered.filter(tags__name__in=tags)
        if feed_tags:
            feeds = models.UserFeed.objects.filter(tags__name__in=feed_tags)
            semi_filtered = semi_filtered.filter(feed__in=feeds)
        return semi_filtered

    def apply_sorting(self, obj_list, options=None):
        '''Workaround: we don't want to expose the implementation detail that
        we're returning UserFeedItems but ordering on FeedItem.published, so
        we do this seemingly hacky but also very clever thing. It's less of a
        hack because I'm totally documenting it.
        '''
        custom_ordering = None
        if 'order_by' in options:
            custom_ordering = options.get('order_by')
            if custom_ordering == 'published':
                custom_ordering = 'item__published'
            elif custom_ordering == '-published':
                custom_ordering = '-item__published'
            else:
                raise InvalidSortError(
                    "The '%s' field does not allow ordering." % custom_ordering)

        qs = super(UserFeedItemResource, self).apply_sorting(obj_list, None)

        if custom_ordering:
            return qs.order_by(custom_ordering)
        return qs

    def get_object_list(self, request):
        return super(UserFeedItemResource, self).get_object_list(request).filter(
            user=request.user.pk)

    def dehydrate(self, bundle):
        bundle.data['description'] = bundle.obj.item.description
        bundle.data['link'] = bundle.obj.item.link
        bundle.data['published'] = bundle.obj.item.published
        bundle.data['title'] = bundle.obj.item.title

        # Shortcut methods, so we don't need relations.
        bundle.data['feed_title'] = bundle.obj.feed.title
        bundle.data['feed_id'] = models.UserFeed.objects.get(
            user=bundle.obj.user, feed=bundle.obj.feed).pk

        bundle.data['tags'] = [tag.name for tag in bundle.obj.tags.all()]
        return bundle
