from datetime import datetime
import json
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from tastypie.test import ResourceTestCase

from raven.models import Feed, FeedItem, UserFeedItem
from raven.test_utils import network_available

User = get_user_model()

__all__ = [
    'API095Test', 'UserFeedResourceTest', 'UserFeedItemResourceTest',
    'FeedResource09Test', 'FeedItemResource09Test',
    ]


class API095TestCase(ResourceTestCase):
    '''A generic test case for API 0.9.5'''

    def setUp(self):
        super(API095TestCase, self).setUp()

        self.user = User.objects.create_user(
            'bob', 'bob@example.com', password='bob')
        self.user.save()

        self.api_client.client.login(username='bob@example.com', password='bob')


class API095Test(API095TestCase):
    '''Test the 0.9.5 api endpoints.'''

    def test_endpoint(self):
        '''The root API endpoint returns all the other endpoints.'''
        result = self.api_client.get('/api/0.9.5/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['feed', 'item'])
        self.assertEqual(content['feed'].keys(), ['list_endpoint', 'schema'])
        self.assertEqual(content['feed']['list_endpoint'], '/api/0.9.5/feed/')


class UserFeedResourceTest(API095TestCase):
    '''Test raven.resources.UserFeedResource.'''

    def test_endpoint_empty(self):
        '''Don't return any feeds if none exist (duh).'''
        result = self.api_client.get('/api/0.9.5/feed/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 0)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)
        self.assertEqual(content['objects'], [])

    def test_endpoint_single_item(self):
        '''The root feed endpoint returns a list of feeds.'''
        feed = Feed.create_and_subscribe(
            'Paul Hummer', 'http://www.paulhummer.org/rss', None, self.user)

        result = self.api_client.get('/api/0.9.5/feed/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 1)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)

        feed_dict = content['objects'][0]
        self.assertEqual(feed_dict.keys(), ['id', 'resource_uri'])

    def test_endpoint_only_owned(self):
        '''Don't return items where UserFeed.user is not the user.'''
        # Test data
        feed = Feed.create_and_subscribe(
            'Paul Hummer', 'http://www.paulhummer.org/rss', None, self.user)

        mike = User.objects.create_user(
            'mike', 'mike@example.com', password='mike')
        mike.save()
        feed = Feed.create_and_subscribe(
            'Gothamist', 'http://feeds.gothamistllc.com/gothamist05', None, mike)

        # Actual test
        result = self.api_client.get('/api/0.9.5/feed/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 1)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)

        feed_dict = content['objects'][0]
        self.assertEqual(feed_dict.keys(), ['id', 'resource_uri'])

    def test_endpoint_paging(self):
        '''Page out more than 20 feeds.'''
        # Test data
        for i in xrange(0, 50):
            Feed.create_and_subscribe(
                'feed {0}'.format(i),
                'http://www.example.com/rss{0}'.format(i),
                None, self.user)

        # Actual test
        result = self.api_client.get('/api/0.9.5/feed/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 50)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(
            content['meta']['next'].split('?')[1],
            'limit=20&offset=20')
        self.assertEqual(len(content['objects']), 20)


class UserFeedItemResourceTest(API095TestCase):
    '''Test raven.resources.UserFeedItemResource.'''

    def test_endpoint_empty(self):
        '''Don't return any items if none exist (uh, duh).'''
        result = self.api_client.get('/api/0.9.5/item/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 0)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)
        self.assertEqual(content['objects'], [])

    def test_endpoint_single_item(self):
        '''The root feed endpoint returns a list of items.'''
        # Test data
        feed = Feed.create_and_subscribe(
            'Paul Hummer', 'http://www.paulhummer.org/rss', None, self.user)
        item = FeedItem()
        item.feed = feed
        item.title = 'Feed title'
        item.link = 'http://www.paulhummer.org/rss/1'
        item.guid = 'http://www.paulhummer.org/rss/1'
        item.published = datetime.now()
        item.save()

        # Actual test
        result = self.api_client.get('/api/0.9.5/item/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 1)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)

        feed_dict = content['objects'][0]
        self.assertEqual(
            sorted(feed_dict.keys()),
            ['id', 'read', 'resource_uri', 'starred'])

    def test_endpoint_only_owned(self):
        '''Don't return items where UserFeedItem.user is not the user.'''
        # Test data
        feed = Feed.create_and_subscribe(
            'Paul Hummer', 'http://www.paulhummer.org/rss', None, self.user)
        item = FeedItem()
        item.feed = feed
        item.title = 'Feed title'
        item.link = 'http://www.paulhummer.org/rss/1'
        item.guid = 'http://www.paulhummer.org/rss/1'
        item.published = datetime.now()
        item.save()

        mike = User.objects.create_user(
            'mike', 'mike@example.com', password='mike')
        mike.save()
        feed = Feed.create_and_subscribe(
            'Gothamist', 'http://feeds.gothamistllc.com/gothamist05', None, mike)
        item = FeedItem()
        item.feed = feed
        item.title = 'Feed title'
        item.link = 'http://www.gothamist.com/rss/1'
        item.guid = 'http://www.gothamist.com/rss/1'
        item.published = datetime.now()
        item.save()

        # Actual test
        result = self.api_client.get('/api/0.9.5/item/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 1)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(content['meta']['next'], None)

    def test_endpoint_paging(self):
        '''Page out more than 20 items.'''
        # Test data
        feed = Feed.create_and_subscribe(
            'Paul Hummer', 'http://www.paulhummer.org/rss', None, self.user)
        for i in xrange(0, 50):
            item = FeedItem()
            item.feed = feed
            item.title = 'Feed title {0}'.format(i)
            item.link = 'http://www.paulhummer.org/rss/{0}'.format(i)
            item.guid = 'http://www.paulhummer.org/rss/{0}'.format(i)
            item.published = datetime.now()
            item.save()

        # Actual test
        result = self.api_client.get('/api/0.9.5/item/')
        self.assertEqual(200, result.status_code)

        content = json.loads(result.content)
        self.assertEqual(content.keys(), ['meta', 'objects'])
        self.assertEqual(
            content['meta'].keys(),
            ['previous', 'total_count', 'offset', 'limit', 'next'])
        self.assertEqual(content['meta']['previous'], None)
        self.assertEqual(content['meta']['total_count'], 50)
        self.assertEqual(content['meta']['offset'], 0)
        self.assertEqual(content['meta']['limit'], 20)
        self.assertEqual(
            content['meta']['next'].split('?')[1],
            'limit=20&offset=20')
        self.assertEqual(len(content['objects']), 20)


class FeedResource09Test(ResourceTestCase):
    '''Test the FeedResource.'''

    def setUp(self):
        super(FeedResource09Test, self).setUp()

        self.user = User.objects.create_user(
            'bob', 'bob@bob.com', password='bob')
        self.user.save()

        self.client = Client()
        self.client.login(username='bob@bob.com', password='bob')

        self.api_client.client.login(username='bob@bob.com', password='bob')

    def test_empty(self):
        response = self.client.get('/api/0.9/feed/')
        content = json.loads(response.content)

        self.assertEqual(content['objects'], [])

    def test_feeds_but_no_subscriptions(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()

        response = self.client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        objects = content['objects']

        self.assertEqual(len(objects), 0)

    def test_single_resource_list(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        feed.add_subscriber(self.user)

        response = self.client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        objects = content['objects']

        self.assertEqual(len(objects), 1)

        feed = Feed.objects.get(pk=feed.pk)
        resource = objects[0]

        self.assertEqual(resource['description'], feed.description)
        self.assertEqual(resource['title'], feed.title)
        self.assertEqual(resource['link'], feed.link)

        self.assertEqual(
            sorted(resource.keys()),
            [u'description', u'id', u'items', u'link', u'resource_uri', u'title'])

    def test_single_resource(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        feed.add_subscriber(self.user)

        response = self.client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        objects = content['objects']
        resource = objects[0]

        response = self.client.get(resource['resource_uri'])
        content = json.loads(response.content)

        feed = Feed.objects.get(pk=feed.pk)

        self.assertEqual(content['description'], feed.description)
        self.assertEqual(content['title'], feed.title)
        self.assertEqual(content['link'], feed.link)

        self.assertEqual(
            sorted(content.keys()),
            [u'description', u'id', u'items', u'link', u'resource_uri', u'title'])

    def test_unauthorized(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()

        uri = '/api/0.9/feed/{0}'.format(feed.pk)
        response = self.client.get(uri, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_subscribe(self):
        #First, make sure there are no subscribed feeds.
        response = self.api_client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        self.assertEqual(len(content['objects']), 0)

        #Subscribe to a feed.
        response = self.api_client.post(
            '/api/0.9/feed/', format='json',
            data={'link': 'http://paulhummer.org/rss'})
        self.assertEqual(response.status_code, 201)

        #Ensure the feed is accessible via the API now.
        response = self.api_client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        self.assertEqual(len(content['objects']), 1)
        self.assertEqual(
            content['objects'][0]['link'],
            'http://paulhummer.org/rss')

    def test_unsubscribe(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        feed.add_subscriber(self.user)

        #Ensure the user is subscribed.
        response = self.api_client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        self.assertEqual(len(content['objects']), 1)

        response = self.api_client.delete(
            content['objects'][0]['resource_uri'])
        self.assertEqual(response.status_code, 204)

        #Ensure the feed is now deleted.
        response = self.api_client.get('/api/0.9/feed/')
        content = json.loads(response.content)
        self.assertEqual(len(content['objects']), 0)


class FeedItemResource09Test(TestCase):
    '''Test the FeedItemResource.'''

    def setUp(self):
        self.user = User.objects.create_user(
            'bob', 'bob@bob.com', password='bob')
        self.user.save()

        self.client = Client()
        self.client.login(username='bob@bob.com', password='bob')

    def test_empty(self):
        response = self.client.get('/api/0.9/item/')

        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['objects'], [])

    @unittest.skipUnless(network_available(), 'Network unavailable')
    def test_single_resource_list(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.site = 'http://www.paulhummer.org/'
        feed.save()
        feed.update()
        self.user.subscribe(feed)

        response = self.client.get('/api/0.9/item/')
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        objects = content['objects']

        self.assertEqual(len(objects), 20)

        resource = objects[0]
        resource_id = resource['resource_uri'].split('/')[-2]
        item = FeedItem.objects.get(pk=resource_id)

        self.assertEqual(resource['description'], item.description)
        self.assertEqual(resource['title'], item.title)
        self.assertEqual(resource['link'], item.link)

    @unittest.skipUnless(network_available(), 'Network unavailable')
    def test_single_resource(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.site = 'http://www.paulhummer.org/'
        feed.save()
        feed.update()
        self.user.subscribe(feed)

        #Create another feed that the user isn't subscribed to.
        unused_feed = Feed()
        unused_feed.link = 'http://www.chizang.net/alex/blog/feed/'
        unused_feed.site = 'http://www.chizang.net/alex/blog/'
        unused_feed.save()
        unused_feed.update()

        response = self.client.get('/api/0.9/item/')
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        objects = content['objects']
        resource = objects[0]

        response = self.client.get(resource['resource_uri'])
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        resource_id = resource['resource_uri'].split('/')[-2]
        item = FeedItem.objects.get(pk=resource_id)
        useritem = UserFeedItem.objects.get(user=self.user, item=item)

        self.assertEqual(resource['description'], item.description)
        self.assertEqual(resource['link'], item.link)
        self.assertEqual(resource['read'], useritem.read)
        self.assertEqual(resource['title'], item.title)

        feed_id = int(resource['feed']['id'])
        self.assertEqual(feed_id, item.feed.pk)

        self.assertEqual(
            sorted(resource.keys()),
            [u'description', u'feed', u'id', u'link', u'published', u'read',
             u'resource_uri', u'title'])

    @unittest.skipUnless(network_available(), 'Network unavailable')
    def test_resource_read(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        feed.update()
        feed.add_subscriber(self.user)

        response = self.client.get('/api/0.9/item/')
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        objects = content['objects']
        resource = objects[0]

        response = self.client.get(resource['resource_uri'])
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        resource_id = resource['resource_uri'].split('/')[-2]
        item = FeedItem.objects.get(pk=resource_id)
        useritem = UserFeedItem.objects.get(user=self.user, item=item)

        self.assertEqual(resource['read'], False)

        useritem.read = True
        useritem.save()

        response = self.client.get(resource['resource_uri'])
        resource = json.loads(response.content)

        self.assertEqual(resource['read'], True)

    @unittest.skipUnless(network_available(), 'Network unavailable')
    def test_unauthorized(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        self.user.subscribe(feed)

        #Create another feed that the user isn't subscribed to.
        unused_feed = Feed()
        unused_feed.link = 'http://xkcd.com/atom.xml'
        unused_feed.site = 'http://xkcd.com/'
        unused_feed.save()
        unused_feed.update()
        feeditem_id = unused_feed.items.all()[0].pk

        response = self.client.get(
            '/api/0.9/item/{0}'.format(feeditem_id),
            follow=True)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(network_available(), 'Network unavailable')
    def test_resource_put_read(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()
        feed.update()
        feed.add_subscriber(self.user)

        response = self.client.get('/api/0.9/item/')
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)
        objects = content['objects']
        resource = objects[0]

        response = self.client.get(resource['resource_uri'])
        self.assertEqual(response.status_code, 200)

        resource = json.loads(response.content)

        self.assertEqual(resource['read'], False)

        resource['read'] = True

        self.client.put(
            resource['resource_uri'],
            data=json.dumps(resource),
            content_type='application/json')

        response = self.client.get(resource['resource_uri'])
        resource = json.loads(response.content)
        self.assertEqual(resource['read'], True)
