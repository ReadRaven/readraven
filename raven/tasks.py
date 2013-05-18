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

    def _import_subscriptions(self):
        name = os.path.join(
            os.path.splitext(os.path.basename(self.filename))[0],
            'Reader', 'subscriptions.xml')
        try:
            subscriptions = opml.from_string(self.z.open(name).read())
        except KeyError:
            return False

        for sub in subscriptions:
            if hasattr(sub, 'type'):
                title = sub.title
                link = sub.xmlUrl
                site = sub.htmlUrl
                Feed.create_and_subscribe(title, link, site, self.user)
            else:
                # In this case, it's a 'group' of feeds.
                folder = sub
                for sub in folder:
                    title = sub.title
                    link = sub.xmlUrl
                    site = sub.htmlUrl
                    feed = Feed.create_and_subscribe(title, link, site, self.user)

                    userfeed = feed.userfeed(self.user)
                    userfeed.tags.add(folder.title)
        return True

    def run(self, user, filename, *args, **kwargs):
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as z:
                self.z = z
                self.user = user
                self.filename = filename

                did_sub = self._import_subscriptions()
            return did_sub
        else:
            return False


class SyncFromReaderAPITask(Task):
    '''A task for sync'ing data from a Google Reader-compatible API.'''

    def run(self, user, *args, **kwargs):
        def _new_user_item(user, feed, entry):
            try:
                item = FeedItem.objects.get(reader_guid=entry.id)
            except ObjectDoesNotExist:
                item = FeedItem()
                item.feed = feed
                item.title = entry.title
                item.link = entry.url
                item.description = entry.content

                item.atom_id = ''
                item.reader_guid = entry.id
                item.published = datetime.utcfromtimestamp(entry.time)
                item.guid = item.calculate_guid()
                item.save()

            try:
                user_item = item.userfeeditem(user)
            except ObjectDoesNotExist:
                # Nasty. The above only works if a user is actually
                # subscribed to a feed. However, it can be the case
                # where we're trying to import Google Reader, and we're
                # processing items that have been shared with us. In
                # this case, we probably won't be subscribed to the
                # feed, and more, we probably don't want to subscribe to
                # the feed. So manually create a UserFeedItem so the
                # Item can be accessed by the User. We can pull it out
                # of the db later by searching for the 'shared-with-you'
                # tag.
                user_item = UserFeedItem()
                user_item.item = item
                user_item.user = user
                user_item.feed = feed
                user_item.save()

            user_item.read = entry.read
            user_item.starred = entry.starred
            for t in entry.tags:
                user_item.tags.add(t)
            user_item.save()

            return user_item

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
            feed = Feed.create_and_subscribe(f.title, f.feedUrl, f.siteUrl, user)
            feeds[f.feedUrl] = feed
            userfeed = feed.userfeed(user)
            for c in f.categories:
                userfeed.tags.add(c.label)

        # Next, import all the items from the feeds
        for f in reader.feeds:
            feed = feeds[f.feedUrl]

            f.loadItems(loadLimit=150)
            for e in f.items:
                if e.url is None:
                    continue
                _new_user_item(user, feed, e)

        # Finally, import the special items
        reader.makeSpecialFeeds()
        special = reader.specialFeeds.keys()
        special.remove('read')
        special.remove('reading-list')
        for sf in special:
            f = reader.specialFeeds[sf]
            f.loadItems(loadLimit=150)
            for e in f.items:
                try:
                    feed = feeds[e.feed.feedUrl]
                except KeyError:
                    # Dammit, google. WTF are these beasties?
                    # u'user/00109242490472324272/source/com.google/link'
                    if e.feed.feedUrl.startswith('user/'):
                        link = Feed.autodiscover(e.feed.siteUrl)
                        if not link:
                            link = e.feed.feedUrl
                    feed = Feed.create_raw(e.feed.title, link, e.feed.siteUrl)
                    feeds[e.feed.feedUrl] = feed

                user_item = _new_user_item(user, feed, e)

                if sf == 'like':
                    user_item.tags.add('imported', 'liked')
                elif sf == 'post' or sf == 'created':
                    user_item.tags.add('imported', 'notes')
                elif sf == 'broadcast':
                    user_item.tags.add('imported', 'shared')
                elif sf == 'broadcast-friends':
                    user_item.tags.add('imported', 'shared-with-you')
                elif sf == 'starred':
                    user_item.tags.add('imported')

                user_item.save()

        return True
