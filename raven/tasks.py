from datetime import datetime, timedelta
import logging
import os
import zipfile

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage

from celery.task import task, Task, PeriodicTask
from libgreader import ClientAuthMethod, OAuth2Method, GoogleReader
import json
import opml

from raven.models import Feed, FeedItem, UserFeedItem

logger = logging.getLogger('django')


class FakeEntry(object):
    def __init__(self, item):
        self.read = False
        self.starred = False
        self.tags = []

        self.id = item['id']
        self.title = item['title']
        self.url = item['url']
        self.content = item['content']
        self.time = item['time']

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
        try:
            paranoid_item = FeedItem.objects.get(guid=item.guid)
            item = paranoid_item
            logger.warn('Detected duplicate GUID for %s' % item.link)
        except ObjectDoesNotExist:
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

@task
def update_feeds(feeds, *args, **kwargs):
    # Touch each feed quickly, in case we do not process the entire
    # queue before the next beat ticks.
    for feed in feeds:
        feed.last_fetched = datetime.utcnow()
        feed.save()

    for feed in feeds:
        feed.update(hack=kwargs.get('hack', False))

class UpdateFeedBeat(PeriodicTask):
    '''A task for updating a set of feeds.'''

    SLICE_SIZE = 200
    run_every = timedelta(seconds=60*5)

    def run(self):
        for freq in [Feed.FETCH_FAST, Feed.FETCH_DEFAULT, Feed.FETCH_SLOW]:
            age = datetime.utcnow() - timedelta(minutes=freq)
            feeds = Feed.objects.filter(last_fetched__lt=age,
                                        fetch_frequency=freq)[:self.SLICE_SIZE]
            update_feeds.apply_async([feeds])

        # If we imported feeds + feeditems from Reader, we have
        # never marked them as fetched. So we find them here and
        # fetch them for the first time. But as feedparser goes out
        # and grabs feeds, there is absolutely no way to map those
        # feeditems to the ones we've already grabbed from Reader.
        #
        # We do actually want those feeditems in our database, which
        # is why we don't skip the update here. But we also don't
        # want tons of duplicate or weird old entries to appear in
        # the users' feeds.
        #
        # So we pass 'hack' and we use the heuristic where if the
        # feeditem from feedparser is *older* than the most recent
        # Reader imported feeditem, then import it but also mark it
        # as read.
        #
        # Wow.
        never_fetched = Feed.objects.filter(last_fetched=None)
        update_feeds.apply_async([never_fetched], { 'hack' : True })

class EatTakeoutTask(Task):
    '''A task for processing a Google Takeout file.'''

    def _import_subscriptions(self):
        subscriptions = None
        for f in self.z.namelist():
            if 'subscriptions.xml' in f:
                subscriptions = opml.from_string(self.z.open(f).read())
                break

        if subscriptions is None:
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

    def _import_json_items(self, import_file):
        data = None
        for f in self.z.namelist():
            if import_file in f:
                data = json.loads(self.z.open(f).read(), strict=False)
                break

        if data is None:
            return False

        try:
            # This is like, weak sauce verification, hoping that we're
            # not about to get bogus data. Still, a carefully crafted
            # attack file could make it past this check.
            id = data['id']
            if not (id.endswith('starred') or
                    id.endswith('broadcast-friends') or
                    id.endswith('broadcast') or
                    id.endswith('post') or
                    id.endswith('like')):
                return False
        except KeyError:
            return False

        for i in data['items']:
            title = i['origin']['title']
            site = i['origin']['htmlUrl']
            link = i['origin']['streamId']
            if link.startswith('feed/'):
                link = link.replace('feed/', '', 1)
            # These are some weird bullshit links created by google
            # reader. Try and discover a real link instead.
            elif link.startswith('user/'):
                maybe = Feed.autodiscover(site)
                if maybe:
                    link = maybe

            feed = Feed.create_raw(title, link, site)

            item = {}
            item['id'] = i['id']
            item['title'] = i['title']
            item['url'] = i.get('canonical', i.get('alternate', ''))[0]['href']
            try:
                item['content'] = i['content']['content']
            except KeyError:
                try:
                    item['content'] = i['summary']['content']
                except KeyError:
                    # No idea if this is even possible, we should squawk
                    item['content'] = ''
            item['time'] = i['published']
            entry = FakeEntry(item)
            user_item = _new_user_item(self.user, feed, entry)

            for c in i.get('categories', []):
                if c.startswith('user/') and c.endswith('/like'):
                    user_item.tags.add('liked')
                elif c.startswith('user/') and c.endswith('/post'):
                    user_item.tags.add('notes')
                elif c.startswith('user/') and c.endswith('/created'):
                    user_item.tags.add('notes')
                # Annoyingly, if something is shared-with-you, it also
                # gets the /broadcast tag. So if we are processing the
                # shared-with-you.json file, don't mark those items as
                # things that *you've* shared
                elif c.startswith('user/') and c.endswith('/broadcast') \
                    and not id.endswith('broadcast-friends'):
                    user_item.tags.add('shared')
                elif c.startswith('user/') and c.endswith('/broadcast-friends'):
                    user_item.tags.add('shared-with-you')
                elif c.startswith('user/') and c.endswith('/starred'):
                    user_item.starred = True
                elif c.startswith('user/') and c.endswith('/read'):
                    user_item.read = True
                elif c.startswith('user/') and ('label' in c):
                    tag = c.split('/')[-1]
                    user_item.tags.append(tag)

            user_item.tags.add('imported')
            user_item.save()

            try:
                # This comes from the 'shared-with-you' category.
                friend_userid = i['via'][0]['href'].split('/')[-4]
                # Not sure how to save/model friend_userid yet
            except KeyError:
                pass

            # XXX: should we do something about i['comments'] too?
            for a in i['annotations']:
                # Following attributes are interesting, but not sure
                # how to model them yet.
                #  - a['content']
                #  - a['userId']
                #  - a['profileId']
                pass

    def run(self, user, filename, *args, **kwargs):
        local = default_storage.open(filename)
        if zipfile.is_zipfile(local):
            with zipfile.ZipFile(local, 'r') as z:
                self.z = z
                self.user = user
                self.filename = filename

                did_sub = self._import_subscriptions()
                if not did_sub:
                    # Probably a malformed takeout. Let's stop processing
                    # immediately.
                    return did_sub

                imports = [
                    'starred.json',
                    'shared-by-followers.json',
                    'shared.json',
                    'notes.json',
                    'liked.json',
                ]
                for i in imports:
                    self._import_json_items(i)
            return True
        else:
            return False


class SyncFromReaderAPITask(Task):
    '''A task for sync'ing data from a Google Reader-compatible API.'''

    def run(self, user, loadLimit, *args, **kwargs):
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

        try:
            reader.buildSubscriptionList()
        except TypeError, exc:
            SyncFromReaderAPITask().retry(exc=exc)

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

            f.loadItems(loadLimit=loadLimit)
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
            f.loadItems(loadLimit=1000)
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
