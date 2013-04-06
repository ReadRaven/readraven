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


class UpdateFeedTask(PeriodicTask):
    '''A task for updating a set of feeds.'''

    SLICE_SIZE = 100
    run_every = timedelta(seconds=60*5)

    def run(self):
        age = datetime.now() - timedelta(minutes=30)
        feeds = Feed.objects.filter(last_fetched__lt=age)[:self.SLICE_SIZE]

        for feed in feeds:
            feed.update()
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
                        feed = Feed.create_from_url(sub.xmlUrl, user)
                    else:
                        # TODO: it makes sense to handle Reader's 'groups'
                        folder = sub
                        for sub in folder:
                            feed = Feed.create_from_url(sub.xmlUrl, user)
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
            feed = Feed.create_from_url(f.feedUrl, user)

        # TODO: here, we should suck in all the other metadata

        return True

