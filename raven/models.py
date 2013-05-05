from datetime import datetime
import logging
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError

from taggit.managers import TaggableManager

import feedparser
import hashlib

logger = logging.getLogger('django')
User = get_user_model()


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

    feed = models.ForeignKey('Feed', related_name='userfeeds')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeds')
    tags = TaggableManager()


class UserFeedItem(models.Model):
    '''A model for user metadata on a post.'''

    class Meta:
        unique_together = ('user', 'item',)
        index_together = [
            ['user', 'feed', 'read', 'item'],
        ]

    item = models.ForeignKey('FeedItem', related_name='userfeeditems')
    feed = models.ForeignKey('Feed', related_name='feeditems')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeditems')

    read = models.BooleanField(default=False)
    tags = TaggableManager()


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
    link = models.URLField(max_length=500, unique=True)
    title = models.CharField(max_length=200)

    # Optional metadata
    generator = models.CharField(max_length=100, blank=True)

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
        userfeed = UserFeed()
        userfeed.feed = self
        userfeed.user = subscriber
        try:
            userfeed.validate_unique()
        except ValidationError:
            return

        userfeed.save()

        for item in self.items.all():
            user_item = UserFeedItem()
            user_item.item = item
            user_item.user = subscriber
            user_item.feed = self
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
    def create_basic(Class, title, link, subscriber):
        feed = Class()
        feed.title = title
        feed.link = link

        try:
            feed.validate_unique()
        except ValidationError:
            feed = Feed.objects.get(link=link)
        else:
            feed.save()  # Save so that Feed has a key
            feed.add_subscriber(subscriber)
        finally:
            return feed

    @classmethod
    def create_from_url(Class, url, subscriber):
        data = feedparser.parse(url)
        if data.bozo is not 0 or data.status == 301:
            return None

        return Class.create_basic(data.feed.title, data.feed.link, subscriber)

    def update(self, data=None):
        if data is None:
            data = feedparser.parse(self.link)

        updated = False
        try:
            if self.title is not data.feed.title:
                self.title = data.feed.title
                updated = True
        except AttributeError:
            logger.debug('Potential problem with feed id: %s' % self.pk)
            if data.bozo == 1:
                logger.debug('Exception is %s' % data.bozo_exception)
        try:
            if self.description is not data.feed.description:
                self.description = data.feed.description
                updated = True
        except AttributeError:
            logger.debug('Potential problem with feed id: %s' % self.pk)
            if data.bozo == 1:
                logger.debug('Exception is %s' % data.bozo_exception)
        try:
            if self.generator is not data.feed.generator:
                self.generator = data.feed.generator
                updated = True
        except AttributeError:
            pass
        if updated:
            self.save()

        for entry in data.entries:
            item = FeedItem()
            item.feed = self
            try:
                item.description = entry.summary
            except AttributeError:
                logger.debug('Potential problem with feed id: %s' % self.pk)
                if data.bozo == 1:
                    logger.debug('Exception is %s' % data.bozo_exception)
            try:
                item.link = entry.link
            except AttributeError:
                logger.debug('Potential problem with feed id: %s' % self.pk)
                if data.bozo == 1:
                    logger.debug('Exception is %s' % data.bozo_exception)
            try:
                item.atom_id = entry.id
            except AttributeError:
                # Set this to empty string so calculate_guid() doesn't die
                item.atom_id = ''
                logger.debug('Potential problem with feed id: %s' % self.pk)
                if data.bozo == 1:
                    logger.debug('Exception is %s' % data.bozo_exception)
            try:
                if entry.published_parsed is None:
                    # In this case, there's a "date", but it's unparseable,
                    # i.e. it's something silly like "No date found",
                    # which isn't a date.
                    item.published = datetime.utcnow()
                else:
                    # This warns about naive timestamps when timezone
                    # support is enabled.
                    item.published = datetime.utcfromtimestamp(
                        time.mktime(entry.published_parsed))
            except AttributeError:
                # Ugh. Some feeds don't have published dates...
                item.published = datetime.utcnow()
            try:
                item.title = entry.title
            except AttributeError:
                # Fuck you LiveJournal.
                item.title = u'(none)'

            item.guid = item.calculate_guid()
            try:
                item.validate_unique()
            except ValidationError:
                item = FeedItem.objects.get(guid=item.guid)
            else:
                item.save()

            for user in self.subscribers.all():
                user_item = UserFeedItem()
                user_item.user = user
                user_item.item = item
                user_item.feed = self
                user_item.save()

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

    feed = models.ForeignKey(Feed, related_name='items')

    # Required properties
    description = models.TextField()
    # It's possible to have longer urls, but anything longer than 2083
    # characters will break in IE.
    link = models.URLField(max_length=500)
    title = models.TextField()

    # Various GUIDs
    #   guid        - internally calculated
    #   atom_id     - supplied by feedparser, optional
    guid = models.CharField(max_length=128, unique=True)
    atom_id = models.CharField(max_length=500, null=True)

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
        guid.update(self.feed.link)
        guid.update(self.link)
        guid.update(self.atom_id)
        guid.update(self.title.encode('utf-8'))

        epoch = datetime(1970, 1, 1)
        guid.update(str(int((self.published - epoch).total_seconds())))
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
