from datetime import datetime, timedelta
import os
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from raven import tasks
from raven.models import Feed, UserFeedItem
from raven.test_utils import network_available

THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, 'testdata')
SECURE_FILE = os.path.join(THIS_DIR, '..', '..', 'secure')

User = get_user_model()

__all__ = [
    'UpdateFeedTaskTest', 'ImportOPMLTaskTest', 'SyncFromReaderAPITaskTest']


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
        self.assertEqual(total_feeds, 123)
        self.assertEqual(owner.feeds.count(), total_feeds-1)

        starred = UserFeedItem.objects.filter(starred=True)
        self.assertEqual(len(starred), 9)

        imported = UserFeedItem.objects.filter(tags__name__in=['imported'])
        self.assertEqual(len(imported), 9)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_nasty(self):
        owner = User()
        owner.email = 'Bob'
        owner.save()

        # A zip bomb
        task = tasks.ImportOPMLTask()
        result = task.delay(owner, os.path.join(TESTDATA_DIR, '42.zip'))

        # Tricksy! The celery task should succeed in running, but should
        # return a Failed (False) result
        self.assertTrue(result.successful())
        self.assertFalse(result.result)


class SyncFromReaderAPITaskTest(TestCase):
    '''Test SyncFromReaderAPITask.'''

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @unittest.skipUnless(os.path.exists(SECURE_FILE), 'password unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        with open(SECURE_FILE) as f:
            secure = f.read()

        owner = User()
        owner.email = 'Alex'
        owner.save()

        other_owner = User()
        other_owner.email = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.save()
        other_owner.subscribe(other_feed)

        task = tasks.SyncFromReaderAPITask()
        result = task.delay(owner, 10, 'alex@chizang.net', secure)

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        # Tricky. We are subscribed to 122 feeds
        # We create another feed above, to get to 123
        # But 3 feeds in the import were "shared-with-you" so the total
        # number of feeds should be 126
        self.assertEqual(feeds.count(), 126)

        total_feeds = Feed.objects.all().count()
        owner = User.objects.get(pk=owner.pk)
        # Verify that we do not get subscribed to feeds when items are
        # 'shared-with-you'.
        self.assertEqual(owner.feeds.count(), 122)

        # Ensure create_raw() won't create a duplicate feed
        title = u'A Softer World'
        link = u'http://www.rsspect.com/rss/asw.xml'
        site = u'http://www.asofterworld.com'

        feed = Feed.objects.get(link=link)
        duplicate = Feed.create_raw(title, link, site)
        duplicate.add_subscriber(owner)
        self.assertEqual(feed.pk, duplicate.pk)

        # Testing that subscribing a second time doesn't blow up.
        duplicate2 = Feed.create_and_subscribe(title, link, site, owner)
        self.assertEqual(feed.pk, duplicate2.pk)

        tagged = UserFeedItem.objects.filter(tags__name__in=['shared-with-you'])
        self.assertEqual(len(tagged), 10)

        # Uncomment for manual checking of ephemeral data sets
        #from raven.models import FeedItem
        #total_items = FeedItem.objects.all().count()
        #print total_items
