from datetime import datetime
import unittest

from django.contrib.auth import get_user_model
from django.db import IntegrityError, DatabaseError, connection
from django.test import TestCase
from django.test.utils import override_settings

from raven.models import Feed, FeedItem, UserFeedItem
from raven.test_utils import network_available

User = get_user_model()

__all__ = ['UserTest', 'FeedTest', 'FeedItemTest', 'UserFeedItemTest']


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

    def test_normalize_email(self):
        # Built-in email normalization is pretty weak; it only
        # lower-cases the domain part of an email address; doesn't do
        # any additional error checking
        user = User.objects.create_user('Edgar', 'edgar@POE.com')
        self.assertEquals(user.email, 'edgar@poe.com')

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

    @unittest.skipUnless(network_available(), 'Network unavailable')
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


class FeedItemTest(TestCase):
    '''Tests for the FeedItem model.'''

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_for_user(self):
        '''Test FeedItemManager.for_user.'''
        user = User()
        user.email = 'abc@123.come'
        user.save()

        feed = Feed()
        feed.link = 'http://paulhummer.org/rss'
        feed.save()
        user.subscribe(feed)

        other_feed = Feed()
        other_feed.link = 'http://www.chizang.net/alex/blog/feed/'
        other_feed.save()

        userfeeditems = FeedItem.objects.for_user(user)
        self.assertEqual(userfeeditems.count(), feed.items.count())

        other_feed.add_subscriber(user)

        userfeeditems = FeedItem.objects.for_user(user)
        self.assertEqual(
            userfeeditems.count(),
            feed.items.count() + other_feed.items.count())


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
