from datetime import datetime
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from raven.models import Feed, FeedItem, UserFeed, UserFeedItem
from raven.test_utils import network_available

User = get_user_model()

__all__ = ['FeedTest', 'FeedItemTest', 'UserFeedTest', 'UserFeedItemTest']


class FeedTest(TestCase):
    '''Test the Feed model.'''

    def setUp(self):
        self.user = User()
        self.email = 'edgar@poe.com'
        self.user.save()

    def test_subscribers(self):
        bob = User()
        bob.email = 'Bob'
        bob.save()
        steve = User()
        steve.email = 'Steve'
        steve.save()

        feed = Feed()
        feed.title = 'Some Political Bullshit'
        feed.link = 'http://bs.com/rss'
        feed.site = 'http://bs.com'
        feed.save()
        feed.add_subscriber(bob)
        feed.add_subscriber(steve)

        other_feed = Feed()
        other_feed.title = 'Mom\'s recipe blog'
        other_feed.site = 'http://yourmom.com'
        other_feed.link = 'http://yourmom.com/rss'
        other_feed.save()
        other_feed.add_subscriber(steve)

        self.assertEqual(feed.subscribers.count(), 2)
        self.assertEqual(other_feed.subscribers.count(), 1)

    def test_add_subscriber(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.link = 'http://boingboing.net'
        feed.save()

        item = FeedItem()
        item.title = 'Octopus v. Platypus'
        item.description = 'A fight to the death.'
        item.link = item.guid = 'http://www.example.com/rss/post'
        item.published = datetime.now()
        item.feed = feed
        item.save()

        # Note carefully... we can safely call add_subscriber at any
        # point after User and Feed creation and be confident that we'll
        # never create duplicate UserFeedItem join table entries.
        #
        # All existing items *before* add_subscriber are added to user
        # during add_subscriber time
        #
        # All new items *after* subscription are added to user during
        # FeedItem post_save() signal
        feed.add_subscriber(user)

        item2 = FeedItem()
        item2.title = 'Cute bunny rabbit video'
        item2.description = 'They die at the end.'
        item2.link = item.guid = 'http://www.example.com/rss/post'
        item2.published = datetime.now()
        item2.feed = feed
        item2.save()

        self.assertEqual(feed.subscribers.count(), 1)
        self.assertEqual(user.feeditems.count(), 2)

    def test_duplicates(self):
        '''Ensure that we can't create duplicate feeds using create_raw()'''
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.link = 'http://boingboing.net/atom.xml'
        feed.site = 'http://boingboing.net'
        f = Feed.create_raw(feed.title, feed.link, feed.site, user)

        feed2 = Feed()
        feed2.title = 'BoingBoing'
        feed2.link = 'http://boingboing.net/atom.xml'
        feed2.site = 'http://boingboing.net'
        # XXX: TODO: we need to add/test duplicate checks save() too :(
        f2 = Feed.create_raw(feed2.title, feed2.link, feed2.site, user)

        self.assertEqual(f.pk, f2.pk)

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_update(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.link = 'http://paulhummer.org/rss'
        feed.save()
        feed.update()

        # Re-fetch the feed
        feed = Feed.objects.get(pk=feed.pk)

        self.assertEqual(feed.items.count(), 20)
        self.assertEqual(feed.title, 'Dapper as...')
        self.assertTrue(feed.description.startswith('Bike rider'))

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_malformed(self):
        owner = User()
        owner.email = 'Bob'
        owner.save()

        other_owner = User()
        other_owner.email = 'Mike'
        other_owner.save()
        other_feed = Feed()
        other_feed.save()
        other_owner.subscribe(other_feed)

        # Lack of title
        title = u'rockmnkey'
        link = u'http://rockmnkey.livejournal.com/data/rss'
        site = u'http://rockmnkey.livejournal.com/'
        feed = Feed.create_raw(title, link, site, owner)

        # Duplicate entries
        title = u'Canonical Voices'
        link = u'http://voices.canonical.com/feed/atom/'
        site = u'http://voices.canonical.com/'
        feed = Feed.create_raw(title, link, site, owner)

        # Lack of atom_id
        title = u'aw\'s blog'
        link = u'http://aw.lackof.org/~awilliam/blog/index.rss'
        site = u'http://aw.lackof.org/~awilliam/blog/'
        feed = Feed.create_raw(title, link, site, owner)

        # Dead feed
        title = u'Clayton - MySpace Blog'
        link = u'http://blog.myspace.com/blog/rss.cfm?friendID=73367402'
        site = None
        feed = Feed.create_raw(title, link, site, owner)

        feeds = Feed.objects.all()
        self.assertEqual(feeds.count(), 5)

        total_feeds = Feed.objects.all().count()
        owner = User.objects.get(pk=owner.pk)
        self.assertEqual(owner.feeds.count(), total_feeds-1)


class UserFeedTest(TestCase):
    '''Test the UserFeed model.'''

    def setUp(self):
        self.user = User()
        self.email = 'edgar@poe.com'
        self.user.save()

    def test_basics(self):
        bob = User()
        bob.email = 'Bob'
        bob.save()
        steve = User()
        steve.email = 'Steve'
        steve.save()

        feed = Feed()
        feed.title = 'Some Political Bullshit'
        feed.link = 'http://bs.com/rss'
        feed.site = 'http://bs.com'
        feed.save()

        other_feed = Feed()
        other_feed.title = 'Mom\'s recipe blog'
        other_feed.link = 'http://yourmom.com/rss'
        other_feed.site = 'http://yourmom.com'
        other_feed.save()

        user_feed = UserFeed()
        user_feed.user = bob
        user_feed.feed = feed
        user_feed.save()

        user_feed2 = UserFeed()
        user_feed2.user = steve
        user_feed2.feed = feed
        user_feed2.save()

        user_feed3 = UserFeed()
        user_feed3.user = steve
        user_feed3.feed = other_feed
        user_feed3.save()

        self.assertEqual(feed.subscribers.count(), 2)
        self.assertEqual(other_feed.subscribers.count(), 1)

        feeds_for_steve = UserFeed.objects.filter(user=steve)
        self.assertEqual(len(feeds_for_steve), 2)

    def test_tagging(self):
        bob = User()
        bob.email = 'Bob'
        bob.save()

        feed = Feed()
        feed.title = 'Some Political Bullshit'
        feed.link = 'http://bs.com/rss'
        feed.site = 'http://bs.com'
        feed.save()
        feed.add_subscriber(bob)

        other_feed = Feed()
        other_feed.title = 'Mom\'s recipe blog'
        other_feed.link = 'http://yourmom.com/rss'
        other_feed.site = 'http://yourmom.com'
        other_feed.save()
        other_feed.add_subscriber(bob)

        userfeed = UserFeed.objects.get(user=bob, feed=feed)
        userfeed.tags.add('politics', 'mom')

        userfeed2 = UserFeed.objects.get(user=bob, feed=other_feed)
        userfeed2.tags.add('mom', 'food')

        self.assertIn('mom', [tag.name for tag in userfeed.tags.all()])
        self.assertIn('politics', [tag.name for tag in userfeed.tags.all()])
        self.assertNotIn('food', [tag.name for tag in userfeed.tags.all()])

        tagged = UserFeed.objects.filter(tags__name__in=['mom'])
        self.assertEquals(len(tagged), 2)

        userfeed.tags.set("test")
        self.assertEquals(len(userfeed.tags.all()), 1)
        self.assertNotIn('mom', [tag.name for tag in userfeed.tags.all()])

        # API claims we can do this safely without raising an exception
        userfeed.tags.remove('mom')

        userfeed.tags.clear()
        self.assertEquals(len(userfeed.tags.all()), 0)


class FeedItemTest(TestCase):
    '''Tests for the FeedItem model.'''

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_for_user(self):
        '''Test FeedItemManager.for_user.'''
        user = User()
        user.email = 'abc@123.com'
        user.save()

        feed = Feed()
        feed.link = 'http://paulhummer.org/rss'
        feed.site = 'http://paulhummer.org/'
        feed.save()
        user.subscribe(feed)

        other_feed = Feed()
        other_feed.link = 'http://www.chizang.net/alex/blog/feed/'
        other_feed.site = 'http://www.chizang.net/alex/blog/'
        other_feed.save()

        userfeeditems = FeedItem.objects.for_user(user)
        self.assertEqual(userfeeditems.count(), feed.items.count())

        other_feed.add_subscriber(user)

        userfeeditems = FeedItem.objects.for_user(user)
        self.assertEqual(
            userfeeditems.count(),
            feed.items.count() + other_feed.items.count())

    @unittest.skipUnless(network_available(), 'Network unavailable')
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory',)
    def test_malformed(self):
        '''Test nasty feeds that we've discovered in the wild'''
        owner = User()
        owner.email = 'Bob'
        owner.save()

        # Really long titles.
        title = u'minimal linux'
        link = u'http://minimallinux.com/rss'
        site = u'http://minimallinux.com/'
        feed = Feed.create_raw(title, link, site, owner)

        # This feed is dead, so we don't expect any items downloaded.
        userfeeditems = FeedItem.objects.for_user(owner)
        self.assertEqual(userfeeditems.count(), 0)

        # Discovered while trying to import from google reader.
        # >>> len(e.title)
        # 857
        item = FeedItem()
        item.feed = feed
        item.title = u'This isn\'t a question but more of a submission for your "enough" poll-type thing.<br>\r\n<br>\r\nI would go with Arch as my main distro. It\u2019s the simplest and easiest to setup of any distro I\u2019ve used.<br>\r\n<br>\r\nMy window manager of choice would be dwm. Amazingly simple and very customizable.<br>\r\n<br>\r\nI would use vim for any text editing I would need to do (which mostly involves programming)<br>\r\n<br>\r\nI would be able to get away with using feh as my image viewer, since I never really need to do any image editing.<br>\r\n<br>\r\nChromium, of course.<br>\r\n<br>\r\nI would use dmenu as my app launcher. Another suckless creation, very simple and very fast.<br>\r\n<br>\r\nDropbox for file syncing.<br>\r\n<br>\r\nPidgin (haven\'t looked that much for something simpler) for AIM.<br>\r\n<br>\r\nI would also need a few programming related things such as ruby, gcc, make, etc.'
        item.link = u'http://minimallinux.com/post/7031884799'
        item.description = u'<p>Nice\u2014good stuff here. I really dig dmenu.</p>'
        item.published = datetime.utcfromtimestamp(1309319839)
        item.atom_id = ''
        item.reader_guid = u'tag:google.com,2005:reader/item/022fe5bb1abdb67a'
        item.guid = item.calculate_guid()
        item.save()

        userfeeditems = FeedItem.objects.for_user(owner)
        self.assertEqual(userfeeditems.count(), 1)

        # Feed with deleted, then republished items. Testing that
        # calculate_guid() is hashing on enough fields to allow us to
        # add these FeedItems to the database in this valid but
        # confusing scenario.
        title = u'Jeff Vyduna'
        link = u'http://invalid.invalid'
        site = u'http://invalid.invalid'
        feed = Feed.create_raw(title, link, site, owner)

        item = FeedItem()
        item.feed = feed
        item.title = u'Does anyone know Hebrew so I can access Facebook?'
        item.link = u'http://blog.jeffvyduna.com/does-anyone-know-hebrew-so-i-can-access-faceb'
        item.description = u'<p>\n          <img src="https://phaven-prod.s3.amazonaws.com/files/image_part/asset/54170/TCyYxjMjvRBb-BqvaoscWjl5G7s/medium_photo.jpg">\n        </p>'
        item.published = datetime.utcfromtimestamp(1367035858)
        item.atom_id = ''
        item.reader_guid = u'tag:google.com,2005:reader/item/2646bc2232535aa2'
        item.guid = item.calculate_guid()
        item.save()

        item2 = FeedItem()
        item2.feed = feed
        item2.title = u'Does anyone know Hebrew so I can access Facebook?'
        item2.link = u'http://blog.jeffvyduna.com/does-anyone-know-hebrew-so-i-can-access-faceb'
        item2.description = u'<p>\n\t<div>\n<a href="http://getfile4.posterous.com/getfile/files.posterous.com/jeff/nNppFvf3RyxHnzrzEv2qh0MZjTvm60DFWhmtgZX6YoSiwwrc6GEoWKaJyIt2/photo.jpg"><img alt="Photo" height="334" src="http://getfile5.posterous.com/getfile/files.posterous.com/jeff/QRSlKVXdpkNzSm5sw49bGvBzcnczXh2eMiRRrX4GyrFLp1N7v1vSlAUWtHQp/photo.jpg.scaled.500.jpg" width="500"></a>\n</div>\n\n\t\n</p>\n\n<p><a href="http://blog.jeffvyduna.com/does-anyone-know-hebrew-so-i-can-access-faceb">Permalink</a> \n\n\t| <a href="http://blog.jeffvyduna.com/does-anyone-know-hebrew-so-i-can-access-faceb#comment">Leave a comment\xa0\xa0\xbb</a>\n\n</p>'
        item2.published = datetime.utcfromtimestamp(1323637539)
        item2.atom_id = ''
        item2.reader_guid = u'tag:google.com,2005:reader/item/b9e84d464361f1ac'
        item2.guid = item2.calculate_guid()
        item2.save()

        userfeeditems = FeedItem.objects.for_user(owner)
        self.assertEqual(userfeeditems.count(), 3)


class UserFeedItemTest(TestCase):
    '''Test the UserFeedItem model.'''

    def test_basics(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.link = 'http://boingboing.net'
        feed.save()
        feed.add_subscriber(user)

        item = FeedItem()
        item.title = 'Octopus v. Platypus'
        item.description = 'A fight to the death.'
        item.link = item.guid = 'http://www.example.com/rss/post'
        item.published = datetime.now()
        item.feed = feed
        item.save()

        # Saving an item in a feed should automatically result in
        # subscribed users seeing all those new items.
        self.assertEqual(user.feeditems.count(), 1)

    def test_tagging(self):
        user = User()
        user.email = 'Bob'
        user.save()

        feed = Feed()
        feed.title = 'BoingBoing'
        feed.link = 'http://boingboing.net'
        feed.save()
        feed.add_subscriber(user)

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

        userfeeditem = UserFeedItem.objects.get(user=user, item=item)
        userfeeditem.tags.add("cute", "platypus")

        userfeeditem2 = UserFeedItem.objects.get(user=user, item=item2)
        userfeeditem2.tags.add("bunny", "cute")

        self.assertIn('cute', [tag.name for tag in userfeeditem.tags.all()])
        self.assertIn('platypus', [tag.name for tag in userfeeditem.tags.all()])
        self.assertNotIn('bunny', [tag.name for tag in userfeeditem.tags.all()])

        tagged = UserFeedItem.objects.filter(tags__name__in=['cute'])

        self.assertEquals(len(tagged), 2)

        userfeeditem.tags.set("test")
        self.assertEquals(len(userfeeditem.tags.all()), 1)
        self.assertNotIn('cute', [tag.name for tag in userfeeditem.tags.all()])

        # API claims we can do this safely without raising an exception
        userfeeditem.tags.remove('cute')

        userfeeditem.tags.clear()
        self.assertEquals(len(userfeeditem.tags.all()), 0)
