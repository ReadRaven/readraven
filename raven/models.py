from datetime import datetime
from HTMLParser import HTMLParser
import calendar
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from taggit.managers import TaggableManager
from taggit.models import TaggedItem

import feedparser
import hashlib

logger = logging.getLogger('django')
User = get_user_model()


class FeedManager(models.Manager):
    '''A manager for user-specific queries on Feeds.'''

    def for_user(self, user):
        userfeeds = UserFeed.objects.filter(user=user)
        feeds = self.filter(userfeeds__in=userfeeds)
        return feeds


class Feed(models.Model):
    '''A model for representing an RSS feed.'''

    objects = FeedManager()

    last_fetched = models.DateTimeField(null=True)

    # Required properties
    description = models.TextField()

    # link is the RSS feed link
    # site is the "real" web page (not required!)
    link = models.URLField(max_length=1023, unique=True)
    site = models.URLField(max_length=1023, null=True)
    title = models.CharField(max_length=1023)

    # Optional metadata
    generator = models.CharField(max_length=1023, blank=True)

    # Production battlescars
    dead = models.BooleanField(default=False)

    # Values are in minutes
    FETCH_FAST = 5
    FETCH_DEFAULT = 60
    FETCH_SLOW = 60 * 24
    FETCH_PUSH = 0
    FETCH_NEVER = 0
    FETCH_FREQUENCY = (
        (FETCH_FAST, 'fast'),
        (FETCH_DEFAULT, 'default'),
        (FETCH_SLOW, 'slow'),
        (FETCH_PUSH, 'push'),
        (FETCH_NEVER, 'never'),
    )
    fetch_frequency = models.IntegerField(choices=FETCH_FREQUENCY,
                                          default=FETCH_DEFAULT)

    @property
    def subscribers(self):
        userfeeds = UserFeed.objects.filter(feed=self)
        users = User.objects.filter(userfeeds__in=userfeeds)
        return users

    def add_subscriber(self, subscriber):
        '''Add a subscriber to this feed.

        This not only adds an entry in the FeedUser join table, but also
        populates UserFeedItem with unread FeedItems from the feed.
        '''
        userfeed, new = UserFeed.objects.get_or_create(user=subscriber,
                                                       feed=self)

        # Only add the 10 most recent items to the UserFeed. Otherwise,
        # the user will see feeditems from years and years ago, which is
        # not really what anyone wants.
        count = 0
        for item in self.items.order_by('-published'):
            user_item, new = UserFeedItem.objects.get_or_create(user=subscriber, feed=self, item=item)

            if count < 10:
                count = count + 1
            else:
                user_item.read = True

            user_item.save()

    def remove_subscriber(self, subscriber):
        '''Remove a subscriber from the feed.

        Also remove all UserFeedItems.
        '''
        UserFeedItem.objects.filter(user=subscriber, feed=self).delete()
        UserFeed.objects.filter(feed=self, user=subscriber).delete()

    def userfeed(self, user):
        userfeed = UserFeed.objects.get(user=user, feed=self)
        return userfeed

    @classmethod
    def create_raw(Class, title, link, site):
        feed, new = Feed.objects.get_or_create(link=link,
                        defaults = { 'title' : title,
                                     'site' : site })
        return feed

    @classmethod
    def create_and_subscribe(Class, title, link, site, subscriber):
        feed = Class.create_raw(title, link, site)
        feed.add_subscriber(subscriber)
        return feed

    @classmethod
    def create_from_url(Class, url, subscriber):
        data = feedparser.parse(url)
        if data.bozo is not 0 or data.status == 301:
            return None

        return Class.create_and_subscribe(data.feed.title, data.href, data.feed.link, subscriber)

    @classmethod
    def autodiscover(Class, url):
        '''Caution: this goes out to the network and also parses a bunch of
        html, so it may be slow...'''
        import raven.feedfinder as feedfinder

        # TODO: consider logging every time this is None, so we can go
        # build some manual workarounds?
        try:
            return feedfinder.feed(url)
        except feedfinder.TimeoutError:
            return None

    def update(self, data=None, hack=False):
        # dead feeds so far:
        # 22: http://blog.myspace.com/blog/rss.cfm?friendID=73367402
        # 223: http://www.aaronsw.com/2002/feeds/pgessays.rss
        # 663: http://www.finderskeepers.gcgstudios.com/?p=rss
        if self.dead is True:
            return

        if data is None:
            data = feedparser.parse(self.link)

        updated = False
        try:
            if self.title != data.feed.title:
                self.title = data.feed.title
                updated = True
        except AttributeError:
            logger.debug('Potential problem with feed id: %s' % self.pk)
            if data.bozo == 1:
                logger.debug('Exception is %s' % data.bozo_exception)
        try:
            if self.description != data.feed.description:
                self.description = data.feed.description
                updated = True
        except AttributeError:
            logger.debug('Potential problem with feed id: %s' % self.pk)
            if data.bozo == 1:
                logger.debug('Exception is %s' % data.bozo_exception)
        try:
            if self.generator != data.feed.generator:
                self.generator = data.feed.generator
                updated = True
        except AttributeError:
            pass
        if 'links' in data.feed:
            for link in data.feed.links:
                if link.rel == 'hub':
                    logger.warn('Hub detected: %s' % self.pk)
        if updated:
            self.save()

        if hack is True:
            try:
                last_entry = self.items.all().latest('published')
            except ObjectDoesNotExist:
                last_entry = None

        for entry in data.entries:
            tmp = FeedItem()
            tmp.feed = self
            try:
                tmp.description = entry.content[0]['value'].strip()
            except AttributeError:
                try:
                    tmp.description = entry.summary_detail['value'].strip()
                except AttributeError:
                    try:
                        tmp.description = entry.summary.strip()
                    except AttributeError:
                        logger.warn('No content (%s: %s)' % (self.pk, self.link))
                        if data.bozo == 1:
                            logger.warn('Exception is %s' % data.bozo_exception)
                        continue
            try:
                tmp.link = entry.link
            except AttributeError:
                tmp.link = ''
            try:
                tmp.atom_id = entry.id
            except AttributeError:
                # Set this to empty string so calculate_guid() doesn't die
                tmp.atom_id = ''

            hack_extra_sucky = False
            try:
                if entry.published_parsed is None:
                    # In this case, there's a "date", but it's unparseable,
                    # i.e. it's something silly like "No date found",
                    # which isn't a date.
                    hack_extra_sucky = True
                    tmp.published = datetime.utcnow()
                else:
                    # This warns about naive timestamps when timezone
                    # support is enabled.
                    tmp.published = datetime.utcfromtimestamp(
                        calendar.timegm(entry.published_parsed))
            except AttributeError:
                try:
                    if entry.updated_parsed is None:
                        hack_extra_sucky = True
                        tmp.published = datetime.utcnow()
                        logger.warn('%s: updated_parsed broken: %s' %
                                    (self.pk, self.link))
                    else:
                        tmp.published = datetime.utcfromtimestamp(
                            calendar.timegm(entry.updated_parsed))
                except AttributeError:
                    try:
                        if entry.created_parsed is None:
                            hack_extra_sucky = True
                            tmp.published = datetime.utcnow()
                            logger.warn('%s: created_parsed broken: %s' %
                                        (self.pk, self.link))
                        else:
                            tmp.published = datetime.utcfromtimestamp(
                                calendar.timegm(entry.created_parsed))
                    except AttributeError:
                        hack_extra_sucky = True
                        tmp.published = datetime.utcnow()

            try:
                tmp.title = HTMLParser().unescape(entry.title).encode('utf-8')
            except AttributeError:
                # Fuck you LiveJournal.
                tmp.title = u'(none)'

            tmp.guid = tmp.calculate_guid()
            item, new = FeedItem.objects.get_or_create(guid=tmp.guid,
                               feed=tmp.feed,
                               defaults={ 'published': tmp.published,
                                          'description': tmp.description,
                                          'link' : tmp.link,
                                          'atom_id': tmp.atom_id,
                                          'title' : tmp.title })

            mark_as_read = False
            if hack is True and last_entry is not None:
                delta = last_entry.published - item.published
                if delta.days > 0:
                    mark_as_read = True
                elif delta.days < 0 and hack_extra_sucky is True:
                    # We hit this case when the feed being fetched does
                    # not have a date and we stuffed in utcnow()
                    mark_as_read = True

            UserFeedItem.add_to_users(self, item, mark_as_read)


    # Currently unused RSS (optional) properties:
    # category: <category>Filthy pornography</category>
    # cloud: <cloud domain="www...com" port="80" path="/RPC"
    #               registerProcedure="NotifyMe" protocol="xml-rpc">
    # copyright: <copyright>1871 Copyright Troll</copyright>
    # docs: <docs>http://...</docs>
    # image: <image>
    #           <url>http://...jpg</url>
    #           <title>Image title</title>
    #           <link>http://...</url>
    #        <image>
    # language: <language>en-us</language>
    # lastBuildDate: <lastBuildDate>Thu, 4 Apr 2013</lastBuildDate>
    # managingEditor: <managingEditor>bob@example.com</managingEditor>
    # pubDate: <pubDate>Thu, 4 Apr 2013</pubDate>
    # skipDays:   <skipDays>
    #               <day>Saturday</day>
    #               <day>Sunday</day>
    #             </skipDays>
    # skipHours:  <skipHours>
    #               <hour>0</hour>
    #             </skipHours>
    # textInput:  <textinput>
    #               <description>Search Google</description>
    #               <title>Search</title>
    #               <link>http://www.google.no/search?</link>
    #               <name>q</name>
    #             </textinput>
    # ttl: <ttl>60</ttl>
    # webMaster: <webMaster>webmaster@w3schools.com</webMaster>


class FeedItemManager(models.Manager):
    '''A manager for user-specific queries.'''

    def for_user(self, user):
        userfeeditems = UserFeedItem.objects.filter(user=user)
        items = self.filter(userfeeditems__in=userfeeditems)
        return items


class FeedItem(models.Model):
    '''A model for representing an item in a RSS feed.'''

    objects = FeedItemManager()

    class Meta:
        unique_together = ('feed', 'guid')

    feed = models.ForeignKey(Feed, related_name='items')

    # Required properties
    description = models.TextField()
    # It's possible to have longer urls, but anything longer than 2083
    # characters will break in IE.
    link = models.URLField(max_length=1023)
    title = models.TextField()

    # Various GUIDs
    #   guid        - internally calculated
    #   atom_id     - supplied by feedparser, optional
    guid = models.CharField(max_length=128, unique=True)
    atom_id = models.CharField(max_length=500, null=True)

    # Legacy google reader longform unique id
    # https://code.google.com/p/google-reader-api/wiki/ItemId
    reader_guid = models.CharField(max_length=48, unique=True, null=True)

    # Optional metadata
    published = models.DateTimeField(db_index=True)

    def userfeeditem(self, user):
        userfeeditem = UserFeedItem.objects.get(
            user=user, item=self)
        return userfeeditem

    def calculate_guid(self):
        # guid is the sha256 of:
        #   parent feed.link
        #   entry.link
        #   entry.id
        #   entry.title
        guid = hashlib.sha256()
        guid.update(self.feed.link.encode('utf-8'))
        guid.update(self.link.encode('utf-8'))
        guid.update(self.atom_id.encode('utf-8'))
        guid.update(self.title)
        #if self.reader_guid:
            #guid.update(self.reader_guid)
        return guid.hexdigest()

    # Currently unused RSS (optional) properties:
    # author: <author>bob@example.com</author>
    # category: <category>Wholesome pornography</category>
    # comments: <comments>http://.../comments</comments.
    # enclosure: <enclosure url="http://...mp3" length="200"
    #                       type="audio/mpeg" />
    # pubDate: <pubDate>Thu, 4 Apr 2013</pubDate>
    # source: <source url="http://...">Example.com</source>


# User monkeypatches
@property
def feeds(self):
    userfeeds = UserFeed.objects.filter(user=self)
    feeds = Feed.objects.filter(userfeeds__in=userfeeds)
    return feeds
User.feeds = feeds


@property
def feeditems(self):
    userfeeditems = UserFeedItem.objects.filter(user=self)
    feeditems = FeedItem.objects.filter(
        userfeeditems__in=userfeeditems).order_by('published')
    return feeditems
User.feeditems = feeditems


# UserFeed and UserFeedItem are hand-rolled intermediate join tables
# instead of using django's ManyToManyField. We use these because we
# wish to store metadata about the relationship between Users and
# Feeds and FeedItems, such as tags and read state.
class UserFeed(models.Model):
    '''A model for user metadata on a feed.'''

    class Meta:
        unique_together = ('user', 'feed')
        index_together = [
            ['user', 'feed'],
        ]

    feed = models.ForeignKey(Feed, related_name='userfeeds')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeds')
    tags = TaggableManager()

    def unread_count(self):
        '''Return the UserFeedItem unread count.'''
        return UserFeedItem.objects.filter(
            user=self.user, feed=self.feed, read=False).count()

    @staticmethod
    def userfeed_tags(user):
        '''Return all the UserFeed tags for a user.'''
        #ct = ContentType.objects.get_for_model(UserFeed)
        kwargs = {
            "userfeed__in": UserFeed.objects.filter(user=user)
        }
        tags = TaggedItem.tag_model().objects.filter(**kwargs).distinct()
        return tags


class UserFeedItem(models.Model):
    '''A model for user metadata on a post.'''

    class Meta:
        unique_together = ('user', 'feed', 'item',)
        index_together = [
            ['user', 'feed', 'read', 'item'],
        ]

    item = models.ForeignKey(FeedItem, related_name='userfeeditems')
    feed = models.ForeignKey(Feed, related_name='feeditems')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeditems')

    read = models.BooleanField(default=False)
    starred = models.BooleanField(default=False)
    tags = TaggableManager()

    @classmethod
    def add_to_users(Class, feed, item, mark_as_read=False):
        for user in feed.subscribers.all():
            ufi, new = UserFeedItem.objects.get_or_create(user=user, feed=feed, item=item)
            if mark_as_read is True:
                ufi.read = True

            ufi.save()

    @receiver(post_save, sender=FeedItem)
    def feeditem_callback(sender, **kwargs):
        item = kwargs['instance']
        feed = item.feed
        UserFeedItem.add_to_users(feed, item)
