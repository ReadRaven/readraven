from datetime import datetime, timedelta
import os
import time
import zipfile

from celery.task import Task, PeriodicTask
import feedparser
import libgreader
import opml
import pytz

from raven.models import Feed, FeedItem, UserFeedItem


def update_feed(feed):
    '''Given a feed, update it's FeedItems.'''
    data = feedparser.parse(feed.link)

    for entry in data.entries:
        item = FeedItem()
        item.feed = feed
        item.description = entry.summary
        item.guid = entry.link
        try:
            if entry.published_parsed is None:
                # In this case, there's a "date", but it's unparseable, i.e.
                # it's something silly like "No date found", which isn't a
                # date.
                item.published = datetime.utcnow()
            else:
                # This warns about naive timestamps.
                item.published = datetime.utcfromtimestamp(
                    time.mktime(entry.published_parsed)).replace(tzinfo=pytz.UTC)
        except AttributeError:
            # Ugh. Some feeds don't have published dates...
            item.published = datetime.utcnow()
        try:
            item.title = entry.title
        except AttributeError:
            # Fuck you LiveJournal.
            item.title = feed.title
        item.link = entry.link
        item.save()

        for user in feed.users.all():
            user_item = UserFeedItem()
            user_item.user = user
            user_item.item = item
            user_item.save()

def source_URL_to_feed(url, user):
    '''Take a source URL, and return a Feed model.'''
    data = feedparser.parse(url)
    if data.bozo is not 0 or data.status == 301:
        return None
    feed = Feed()
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
    feed.user = user

    feed.save()
    for entry in data.entries:
        item = FeedItem()
        item.feed = feed
        item.description = entry.summary
        item.guid = entry.link
        try:
            if entry.published_parsed is None:
                # In this case, there's a "date", but it's unparseable, i.e.
                # it's something silly like "No date found", which isn't a
                # date.
                item.published = datetime.utcnow()
            else:
                # This warns about naive timestamps.
                item.published = datetime.utcfromtimestamp(
                    time.mktime(entry.published_parsed)).replace(tzinfo=pytz.UTC)
        except AttributeError:
            # Ugh. Some feeds don't have published dates...
            item.published = datetime.utcnow()
        try:
            item.title = entry.title
        except AttributeError:
            # Fuck you LiveJournal.
            item.title = feed.title
        item.link = entry.link
        item.save()
    return feed


class UpdateFeedTask(PeriodicTask):
    '''A task for updating a set of feeds.'''

    SLICE_SIZE = 100
    run_every = timedelta(seconds=60*5)

    def run(self):
        age = datetime.now() - timedelta(minutes=30)
        feeds = Feed.objects.filter(last_fetched__lt=age)[:self.SLICE_SIZE]

        for feed in feeds:
            update_feed(feed)
            feed.last_fetched = datetime.utcnow()
            feed.save()


class ImportOPMLTask(Task):
    '''A task for importing feeds from OPML files.'''

    def run(self, user, filename, *args, **kwargs):
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as z:
                name = os.path.join(
                    os.path.splitext(os.path.basename(filename))[0],
                    'Reader', 'subscriptions.xml')
                subscriptions = opml.from_string(z.open(name).read())
                for sub in subscriptions:
                    if hasattr(sub, 'type'):
                        feed = source_URL_to_feed(sub.xmlUrl, user)
                    else:
                        # TODO: it makes sense to handle Reader's 'groups'
                        folder = sub
                        for sub in folder:
                            feed = source_URL_to_feed(sub.xmlUrl, user)
            return True
        else:
            return False


class ImportFromReaderAPITask(Task):
    '''A task for importing feeds from a Google Reader-compatible API.'''

    def run(self, user, username, passwd, *args, **kwargs):
        # TODO: we should support the more complex auth methods
        auth = libgreader.ClientAuthMethod(username, passwd)
        reader = libgreader.GoogleReader(auth)

        if not reader.buildSubscriptionList():
            # XXX: better error recovery here?
            return False

        for f in reader.feeds:
            feed = source_URL_to_feed(f.feedUrl, user)

        # TODO: here, we should suck in all the other metadata

        return True

