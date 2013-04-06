from datetime import datetime
import os
import unittest

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from raven import tasks
from raven.models import Feed, FeedItem, UserFeedItem


THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, 'testdata')
SECURE_FILE = os.path.join(THIS_DIR, '..', 'secure')


class FeedTests(TestCase):
    '''Test the Feed model.'''

    def setUp(self):
        self.user = User()
        self.user.save()

    def test_feed_users(self):
        bob = User()
        bob.username = 'Bob'
        bob.save()
        steve = User()
        steve.username = 'Steve'
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
        user.username = 'Bob'
        user.save()

        # Okay, finally we can do the test.
        user_feed_item = UserFeedItem()
        user_feed_item.user = user
        user_feed_item.item = item
        user_feed_item.save()

        self.assertEqual(user.items.count(), 1)


class ImportOPMLTaskTest(TestCase):
    '''Test ImportOPMLTask.'''

    @unittest.skipUnless(os.path.exists(SECURE_FILE), 'password unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        owner = User()
        owner.username = 'Bob'
        owner.save()

        other_owner = User()
        other_owner.username = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.user = other_owner
        other_feed.save()

        task = tasks.ImportOPMLTask()
        result = task.delay(
            owner,
            os.path.join(TESTDATA_DIR, 'alex@chizang.net-takeout.zip'))

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 86)

        owner_feeds = Feed.objects.filter(user=owner)
        self.assertEqual(owner_feeds.count(), 85)


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
        owner.username = 'Bob'
        owner.save()

        other_owner = User()
        other_owner.username = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.user = other_owner
        other_feed.save()

        task = tasks.ImportFromReaderAPITask()
        result = task.delay(owner, 'alex@chizang.net', secure)

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 85)

        owner_feeds = Feed.objects.filter(user=owner)
        self.assertEqual(owner_feeds.count(), 84)

