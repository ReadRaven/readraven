import json
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from tastypie.test import ResourceTestCase

from raven.models import Feed, FeedItem, UserFeedItem
from raven.test_utils import network_available

User = get_user_model()

__all__ = ['FeedResourceTest', 'FeedItemResourceTest']


class FeedResourceTest(ResourceTestCase):
    '''Test the FeedResource.'''

    def setUp(self):
        super(FeedResourceTest, self).setUp()

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
            [u'description', u'link', u'resource_uri', u'title'])

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
            [u'description', u'link', u'resource_uri', u'title'])

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


class FeedItemResourceTest(TestCase):
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
        feed.save()
        feed.update()
        self.user.subscribe(feed)

        #Create another feed that the user isn't subscribed to.
        unused_feed = Feed()
        unused_feed.link = 'http://www.chizang.net/alex/blog/feed/'
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

        feed_id = int(resource['feed'].split('/')[-2])
        self.assertEqual(feed_id, item.feed.pk)

        self.assertEqual(
            sorted(resource.keys()),
            [u'description', u'feed', u'link', u'published', u'read',
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

        self.client.put(
            resource['resource_uri'],
            data=json.dumps({'read': True}),
            content_type='application/json')

        response = self.client.get(resource['resource_uri'])
        resource = json.loads(response.content)
        self.assertEqual(resource['read'], True)
