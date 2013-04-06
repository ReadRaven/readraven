from datetime import datetime
import time

from django.contrib.auth.models import User
from django.db import models
import feedparser


class UserFeedItem(models.Model):
    '''A model for user metadata on a post.'''

    class Meta:
        unique_together = ('item', 'user',)

    item = models.ForeignKey('FeedItem', related_name='+')
    user = models.ForeignKey(User, related_name='items')

    read = models.BooleanField(default=False)


class Feed(models.Model):
    '''A model for representing an RSS feed.'''

    users = models.ManyToManyField(User, related_name='feeds')
    last_fetched = models.DateTimeField(null=True)

    # Required properties
    description = models.TextField()
    link = models.URLField(max_length=500)
    title = models.CharField(max_length=200)

    # Optional metadata
    generator = models.CharField(max_length=100, blank=True)

    def add_subscriber(self, subscriber):
        '''Add a subscriber to this feed.

        This not only adds an entry in the FeedUser join table, but also
        populates UserFeedItem with unread FeedItems from the feed.
        '''
        self.users.add(subscriber)

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
            pass
        try:
            feed.generator = data.feed.generator
        except AttributeError:
            pass
        feed.save()  # Save so that Feed has a key

        feed.users.add(subscriber)
        feed.save()

        feed.update(data)
        return feed

    def update(self, data=None):
        if data is None:
            data = feedparser.parse(self.link)

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
                item.title = self.title
            item.link = entry.link
            item.save()

            for user in self.users.all():
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


class FeedItem(models.Model):
    '''A model for representing an item in a RSS feed.'''

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

    # Currently unused RSS (optional) properties:
    # author: <author>bob@example.com</author>
    # category: <category>Wholesome pornography</category>
    # comments: <comments>http://.../comments</comments.
    # enclosure: <enclosure url="http://...mp3" length="200"
    #                       type="audio/mpeg" />
    # pubDate: <pubDate>Thu, 4 Apr 2013</pubDate>
    # source: <source url="http://...">Example.com</source>


# User monkeypatching for syntactic sugar
def subscribe(self, feed):
    feed.add_subscriber(self)
User.subscribe = subscribe
