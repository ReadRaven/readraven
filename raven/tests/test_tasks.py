from datetime import datetime, timedelta
import os
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from raven import tasks
from raven.models import Feed
from raven.test_utils import network_available

THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, 'testdata')
SECURE_FILE = os.path.join(THIS_DIR, '..', '..', 'secure')

User = get_user_model()

__all__ = [
    'UpdateFeedTaskTest', 'ImportOPMLTaskTest', 'ImportFromReaderAPITaskTest']


class UpdateFeedTaskTest(TestCase):
    '''Test UpdateFeedTask.'''

    @unittest.skipUnless(network_available(), 'Network unavailable')
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

    @unittest.skipUnless(network_available(), 'Network unavailable')
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
        owner = User.objects.get(pk=owner.pk)
        self.assertEqual(owner.feeds.count(), total_feeds-1)


class ImportFromReaderAPITaskTest(TestCase):
    '''Test ImportFromReaderAPITask.'''

    @unittest.skipUnless(network_available(), 'Network unavailable')
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
        owner = User.objects.get(pk=owner.pk)
        self.assertEqual(owner.feeds.count(), total_feeds-1)
