from datetime import datetime
import logging
import time

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
import feedparser

from oauth2client.django_orm import FlowField, CredentialsField

from django.conf import settings

logger = logging.getLogger('django')


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=BaseUserManager.normalize_email(email),
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.save()
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=254)
    email = models.EmailField(max_length=254, unique=True, db_index=True)
    flow = FlowField()
    credential = CredentialsField()

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Handle whether the user has a specific permission?"
        return True

    def has_module_perms(self, app_label):
        # Handle whether the user has permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        # Handle whether the user is a member of staff?"
        return self.is_admin

    @property
    def feeds(self):
        userfeeds = UserFeed.objects.filter(user=self)
        feeds = Feed.objects.filter(userfeeds__in=userfeeds)
        return feeds

    @property
    def feeditems(self):
        userfeeditems = UserFeedItem.objects.filter(user=self)
        feeditems = FeedItem.objects.filter(userfeeditems__in=userfeeditems)
        return feeditems

    def subscribe(self, feed):
        feed.add_subscriber(self)


class UserFeed(models.Model):
    '''A model for user metadata on a feed.'''
    feed = models.ForeignKey('Feed', related_name='userfeeds')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeds')


class UserFeedItem(models.Model):
    '''A model for user metadata on a post.'''

    class Meta:
        unique_together = ('item', 'user',)

    item = models.ForeignKey('FeedItem', related_name='userfeeditems')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='userfeeditems')

    read = models.BooleanField(default=False)


class FeedManager(models.Manager):
    '''A manager for user-specific queries on Feeds.'''

    def for_user(self, user):
        userfeeds = UserFeed.objects.filter(user=user)
        feeds = self.filter(userfeeds__in=userfeeds)
        return feeds


class Feed(models.Model):
    '''A model for representing an RSS feed.'''

    last_fetched = models.DateTimeField(null=True)

    # Required properties
    description = models.TextField()
    link = models.URLField(max_length=500)
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
        userfeed.save()

        for item in self.items.all():
            user_item = UserFeedItem()
            user_item.item = item
            user_item.user = subscriber
            user_item.save()

    @classmethod
    def create_from_url(Class, url, subscriber):
        data = feedparser.parse(url)
        if data.bozo is not 0 or data.status == 301:
            return None
        feed = Class()
        feed.title = data.feed.title
        feed.link = data.feed.link
        try:
            feed.description = data.feed.description
        except AttributeError:
            logger.debug('Feed missing a description at %s' % data.feed.link)
        try:
            feed.generator = data.feed.generator
        except AttributeError:
            pass
        feed.save()  # Save so that Feed has a key

        feed.add_subscriber(subscriber)
        feed.save()

        feed.update(data)
        return feed

    def save(self, *args, **kwargs):
        is_new = False
        if not self.pk:
            is_new = True
        super(Feed, self).save(*args, **kwargs)

        if is_new:
            from raven.tasks import UpdateFeedTask
            task = UpdateFeedTask()
            task.delay([self])

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
        if updated:
            self.save()

        for entry in data.entries:
            item = FeedItem()
            item.feed = self
            item.description = entry.summary
            item.guid = entry.link
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
            item.link = entry.link
            item.save()

            for user in self.subscribers.all():
                user_item = UserFeedItem()
                user_item.user = user
                user_item.item = item
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
    title = models.CharField(max_length=200)

    # Optional metadata
    guid = models.CharField(max_length=500)
    published = models.DateTimeField()

    def userfeeditem(self, user):
        userfeeditem = UserFeedItem.objects.get(
            user=user, item=self)
        return userfeeditem

    # Currently unused RSS (optional) properties:
    # author: <author>bob@example.com</author>
    # category: <category>Wholesome pornography</category>
    # comments: <comments>http://.../comments</comments.
    # enclosure: <enclosure url="http://...mp3" length="200"
    #                       type="audio/mpeg" />
    # pubDate: <pubDate>Thu, 4 Apr 2013</pubDate>
    # source: <source url="http://...">Example.com</source>
