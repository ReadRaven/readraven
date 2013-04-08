from datetime import datetime, timedelta
import json
import os
import unittest

from django.db import IntegrityError, DatabaseError, connection
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from raven import tasks
from raven.models import Feed, FeedItem, UserFeedItem


THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, 'testdata')
SECURE_FILE = os.path.join(THIS_DIR, '..', 'secure')

User = get_user_model()

class UserTest(TestCase):
    def test_add_users(self):
        user = User()
        user.username = 'Edgar'
        user.email = 'edgar@poe.com'
        user.save()

        user = User()
        user.username = 'Allan'
        user.email = 'allan@poe.com'
        user.save()

        user = User()
        user.username = 'Edgar'
        user.email = 'edgar@poe.com'
        self.assertRaises(IntegrityError, user.save)

    def test_create_user(self):
        user = User.objects.create_user('Edgar', 'edgar@poe.com')
        user = User.objects.get(email='edgar@poe.com')
        self.assertEquals(user.username, 'Edgar')

        user = User.objects.create_user('Allan', 'allan@poe.com')
        user = User.objects.get(email='allan@poe.com')
        self.assertEquals(user.username, 'Allan')

        self.assertRaises(IntegrityError, User.objects.create_user,
                          'Whoever', 'edgar@poe.com')

    # XXX: Our model should be puking on this but it's not
    @unittest.skip("Not hooked up yet")
    def test_normalize_email(self):
        self.assertRaises(ValueError, User.objects.create_user,
                          'Edgar', 'invalid')

    def test_long_fields(self):
        user = User()
        user.email = 'x' * 254
        self.assertEquals(len(user.email), 254)
        user.save()

        user = User()
        user.email = 'y' * 255
        self.assertEquals(len(user.email), 255)
        self.assertRaises(DatabaseError, user.save)
        # This should probably be its own test somehow
        connection._rollback()

        user = User()
        user.username = 'x' * 254
        self.assertEquals(len(user.username), 254)
        user.email = 'edgar@poe.com'
        user.save()

        user = User()
        user.username = 'x' * 255
        user.email = 'allan@poe.com'
        self.assertRaises(DatabaseError, user.save)

class FeedTest(TestCase):
    '''Test the Feed model.'''

    def setUp(self):
        self.user = User()
        self.email = 'edgar@poe.com'
        self.user.save()

    def test_feed_users(self):
        bob = User()
        bob.email = 'Bob'
        bob.save()
        steve = User()
        steve.email = 'Steve'
        steve.save()

        feed = Feed()
        feed.title = 'Some Political Bullshit'
        feed.save()
        feed.users.add(bob)
        feed.users.add(steve)
        feed.save()

        other_feed = Feed()
        other_feed.title = 'Mom\'s recipe blog'
        other_feed.save()
        other_feed.users.add(steve)
        other_feed.save()

        self.assertEqual(steve.feeds.count(), 2)
        self.assertEqual(bob.feeds.count(), 1)

    def test_add_subscriber(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.save()

        item = FeedItem()
        item.title = 'Octopus v. Platypus'
        item.description = 'A fight to the death.'
        item.link = item.guid = 'http://www.example.com/rss/post'
        item.published = datetime.now()
        item.feed = feed
        item.save()

        item2 = FeedItem()
        item2.title = 'Cute bunny rabbit video'
        item2.description = 'They die at the end.'
        item2.link = item.guid = 'http://www.example.com/rss/post'
        item2.published = datetime.now()
        item2.feed = feed
        item2.save()

        feed.add_subscriber(user)

        self.assertEqual(user.feeds.count(), 1)
        self.assertEqual(user.items.count(), 2)

    def test_user_subscribe(self):
        '''Test the syntactic sugar monkeypatch for User.subscribe.'''
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.save()

        item = FeedItem()
        item.title = 'Octopus v. Platypus'
        item.description = 'A fight to the death.'
        item.link = item.guid = 'http://www.example.com/rss/post'
        item.published = datetime.now()
        item.feed = feed
        item.save()

        item2 = FeedItem()
        item2.title = 'Cute bunny rabbit video'
        item2.description = 'They die at the end.'
        item2.link = item.guid = 'http://www.example.com/rss/post'
        item2.published = datetime.now()
        item2.feed = feed
        item2.save()

        user.subscribe(feed)

        self.assertEqual(user.feeds.count(), 1)
        self.assertEqual(user.items.count(), 2)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_save(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.link = 'http://paulhummer.org/rss'
        feed.save()

        # Re-fetch the feed
        feed = Feed.objects.get(pk=feed.pk)

        self.assertEqual(feed.items.count(), 20)
        self.assertEqual(feed.title, 'Dapper as...')
        self.assertTrue(feed.description.startswith('Bike rider'))


class UserFeedItemTest(TestCase):
    '''Test the UserFeedItem model.'''

    def test_basics(self):
        feed = Feed()
        feed.title = 'BoingBoing'
        feed.save()

        item = FeedItem()
        item.title = 'Octopus v. Platypus'
        item.description = 'A fight to the death.'
        item.link = item.guid = 'http://www.example.com/rss/post'
        item.published = datetime.now()
        item.feed = feed
        item.save()

        user = User()
        user.email = 'Bob'
        user.save()

        # Okay, finally we can do the test.
        user_feed_item = UserFeedItem()
        user_feed_item.user = user
        user_feed_item.item = item
        user_feed_item.save()

        self.assertEqual(user.items.count(), 1)


class FeedResourceTest(TestCase):
    '''Test the FeedResource.'''

    def setUp(self):
        self.client = Client()

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
        self.client = Client()

    def test_empty(self):
        response = self.client.get('/api/0.9/item/')
        content = json.loads(response.content)

        self.assertEqual(content['objects'], [])

    def test_single_resource_list(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()

        response = self.client.get('/api/0.9/item/')
        content = json.loads(response.content)
        objects = content['objects']

        self.assertEqual(len(objects), 20)

        resource = objects[0]
        resource_id = resource['resource_uri'].split('/')[-2]
        item = FeedItem.objects.get(pk=resource_id)

        self.assertEqual(resource['description'], item.description)
        self.assertEqual(resource['title'], item.title)
        self.assertEqual(resource['link'], item.link)

        self.assertEqual(
            sorted(resource.keys()),
            [u'description', u'link', u'published', u'resource_uri', u'title'])

    def test_single_resource(self):
        feed = Feed()
        feed.link = 'http://www.paulhummer.org/rss'
        feed.save()

        response = self.client.get('/api/0.9/item/')
        content = json.loads(response.content)
        objects = content['objects']
        resource = objects[0]

        response = self.client.get(resource['resource_uri'])
        content = json.loads(response.content)

        resource_id = resource['resource_uri'].split('/')[-2]
        item = FeedItem.objects.get(pk=resource_id)

        self.assertEqual(resource['description'], item.description)
        self.assertEqual(resource['title'], item.title)
        self.assertEqual(resource['link'], item.link)

        self.assertEqual(
            sorted(resource.keys()),
            [u'description', u'link', u'published', u'resource_uri', u'title'])


class UpdateFeedTaskTest(TestCase):
    '''Test UpdateFeedTask.'''

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        feed = Feed()
        feed.link = 'http://paulhummer.org/rss'
        last_fetched = datetime.now() - timedelta(minutes=31)
        feed.last_fetched = last_fetched
        feed.save()

        task = tasks.UpdateFeedTask()
        result = task.delay()

        self.assertTrue(result.successful())

        # Re-fetch the feed
        feed = Feed.objects.get(link='http://paulhummer.org/rss')
        self.assertNotEqual(feed.last_fetched, last_fetched)
        self.assertEqual(feed.items.count(), 20)


class ImportOPMLTaskTest(TestCase):
    '''Test ImportOPMLTask.'''

    @unittest.skipUnless(os.path.exists(SECURE_FILE), 'password unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        owner = User()
        owner.email = 'Bob'
        owner.save()

        other_owner = User()
        other_owner.email = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.save()
        other_owner.subscribe(other_feed)

        task = tasks.ImportOPMLTask()
        result = task.delay(
            owner,
            os.path.join(TESTDATA_DIR, 'alex@chizang.net-takeout.zip'))

        self.assertTrue(result.successful())

        total_feeds = Feed.objects.all().count()
        owner = User().objects.get(pk=owner.pk)
        self.assertEqual(owner.feeds.count(), total_feeds-1)


class ImportFromReaderAPITaskTest(TestCase):
    '''Test ImportFromReaderAPITask.'''

    @unittest.skipUnless(os.path.exists(SECURE_FILE), 'password unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        with open(SECURE_FILE) as f:
            secure = f.read()

        owner = User()
        owner.email = 'Bob'
        owner.save()

        other_owner = User()
        other_owner.email = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.save()
        other_owner.subscribe(other_feed)

        task = tasks.ImportFromReaderAPITask()
        result = task.delay(owner, 'alex@chizang.net', secure)

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 85)

        total_feeds = Feed.objects.all().count()
        owner = User().objects.get(pk=owner.pk)
        self.assertEqual(owner.feeds.count(), total_feeds-1)
