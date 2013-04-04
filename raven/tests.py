import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from raven import tasks
from raven.models import Feed


THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, 'testdata')


class ImportOPMLTaskTest(TestCase):
    '''Test ImportOPMLTask.'''

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

        task = tasks.ImportFromReaderAPITask()
        result = task.delay(owner, 'alex@chizang.net', '')

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 85)

        owner_feeds = Feed.objects.filter(user=owner)
        self.assertEqual(owner_feeds.count(), 84)

