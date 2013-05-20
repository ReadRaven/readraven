from datetime import datetime
import os

from django.contrib.auth import get_user_model
from django.db import IntegrityError, DatabaseError, connection
from django.test import TestCase
from django.test.client import Client

from raven.models import Feed, UserFeedItem

THIS_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(THIS_DIR, '..', 'raven', 'tests', 'testdata')

User = get_user_model()


class UserTest(TestCase):
    '''Tests for Raven's custom User class.'''

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

    def test_user_subscribe(self):
        '''Test the syntactic sugar monkeypatch for User.subscribe.'''
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.link = 'http://boingboing.net'
        feed.save()

        unused = Feed()
        unused.title = 'xkcd'
        unused.save()

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
        self.assertEqual(user.feeditems.count(), 2)
        self.assertEqual(user.feeds[0].title, feed.title)

        # Testing we are using order_by() in User.feeditems() monkeypatch
        self.assertEqual(user.feeditems[0].title, item.title)

class ImportTakeoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'bob', 'bob@bob.com', password='bob')
        self.user.save()

        self.client = Client()
        self.client.login(username='bob@bob.com', password='bob')

    def test_import(self):
        takeout = 'alex@chizang.net-takeout.zip'

        # Run this test twice and ensure the counts don't change. That
        # is, ensure we aren't creating duplicates during our imports.
        for i in range(2):
            with open(os.path.join(TESTDATA_DIR, takeout)) as f:
                self.client.post('/usher/import_takeout', {'zipfile' : f })

            total_feeds = Feed.objects.all().count()
            owner = User.objects.get(pk=self.user.pk)

            #self.assertEqual(total_feeds, 145)
            self.assertEqual(self.user.feeds.count(), 122)

            starred = UserFeedItem.objects.filter(starred=True)
            self.assertEqual(len(starred), 9)

            shared_with_me = UserFeedItem.objects.filter(tags__name__in=['shared-with-you'])
            self.assertEqual(len(shared_with_me), 31)

            shared = UserFeedItem.objects.filter(tags__name__in=['shared'])
            self.assertEqual(len(shared), 1)

            # See how all the above should add up!
            imported = UserFeedItem.objects.filter(tags__name__in=['imported'])
            self.assertEqual(len(imported), 41)
