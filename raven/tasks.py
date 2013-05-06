from datetime import datetime, timedelta
import os
import zipfile

from django.core.exceptions import ObjectDoesNotExist

from celery.task import Task, PeriodicTask
from libgreader import ClientAuthMethod, OAuth2Method, GoogleReader
import opml

from raven.models import Feed, FeedItem, UserFeedItem


class UpdateFeedTask(PeriodicTask):
    '''A task for updating a set of feeds.'''

    SLICE_SIZE = 100
    run_every = timedelta(seconds=60*5)

    def run(self, feeds=[]):
        if len(feeds) is 0:
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
                        Feed.create_from_url(sub.xmlUrl, user)
                    else:
                        # In this case, it's a 'group' of feeds.
                        folder = sub
                        for sub in folder:
                            Feed.create_from_url(sub.xmlUrl, user)
            return True
        else:
            return False


class SyncFromReaderAPITask(Task):
    '''A task for sync'ing data from a Google Reader-compatible API.'''

    def run(self, user, *args, **kwargs):
        # user.credential should always be valid when doing oauth2
        if user.credential:
            credential = user.credential
            auth = OAuth2Method(credential.client_id, credential.client_secret)
            auth.authFromAccessToken(credential.access_token)
            auth.setActionToken()
        # username/password auth method, should only be used by our tests
        elif len(args) == 2:
            auth = ClientAuthMethod(args[0], args[1])

        reader = GoogleReader(auth)

        if not reader.buildSubscriptionList():
            # XXX: better error recovery here?
            return False

        feeds = {}
        # First loop quickly creates Feed objects... for speedier UI?
        for f in reader.feeds:
            feed = Feed.create_basic(f.title, f.feedUrl, user)
            feeds[f.feedUrl] = feed
            userfeed = feed.userfeed(user)
            for c in f.categories:
                userfeed.tags.add(c.label)

        for f in reader.feeds:
            feed = feeds[f.feedUrl]

            f.loadItems(loadLimit=5)
            for e in f.items:
                if e.url is None:
                    continue
                try:
                    item = FeedItem.objects.get(reader_guid=e.id)
                except ObjectDoesNotExist:
                    item = FeedItem()
                    item.feed = feed
                    item.title = e.title
                    item.link = e.url
                    item.description = e.content

                    item.atom_id = ''
                    item.reader_guid = e.id
                    item.published = datetime.utcfromtimestamp(e.time)
                    item.guid = item.calculate_guid()
                    item.save()

                user_item = item.userfeeditem(user)
                user_item.read = e.read
                for t in e.tags:
                    user_item.tags.add(t)
                user_item.save()

        # TODO: here, we should suck in all the other metadata

        return True
