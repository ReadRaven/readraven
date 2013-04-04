import os

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
        task = tasks.ImportOPMLTask()
        result = task.delay(
            os.path.join(TESTDATA_DIR, 'alex@chizang.net-takeout.zip'))

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 85)


class ImportFromReaderAPITaskTest(TestCase):
    '''Test ImportFromReaderAPITask.'''

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_run(self):
        task = tasks.ImportFromReaderAPITask()
        result = task.delay('alex@chizang.net', '')

        self.assertTrue(result.successful())

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 84)
