import json
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client

from raven.models import Feed, FeedItem, UserFeedItem
from raven.test_utils import network_available

User = get_user_model()

__all__ = ['FeedResourceTest', 'FeedItemResourceTest']


class FeedResourceTest(TestCase):
    '''Test the FeedResource.'''

    def setUp(self):
        self.user = User.objects.create_user(
            'bob', 'bob@bob.com', password='bob')
        self.user.save()

        self.client = Client()
        self.client.login(username='bob@bob.com', password='bob')

    def test_empty(self):
        response = self.client.get('/api/0.9/feed/')
        content = json.loads(response.content)

        self.assertEqual(content['objects'], [])

    def test_single_resource_list(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()

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
        self.user.subscribe(feed)

        #Create another feed that the user isn't subscribed to.
        unused_feed = Feed()
        unused_feed.link = 'http://www.chizang.net/alex/blog/feed/'
        unused_feed.save()

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
