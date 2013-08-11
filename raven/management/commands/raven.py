from django.core.management.base import BaseCommand
from optparse import make_option

from ...models import Feed

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
    make_option('--kill',
        help='Comma separated list of dead feed primary keys, never to fetch again.',
        dest='dead_feeds'),
    )

    def handle(self, *args, **options):
        if options['dead_feeds']:
            pks = options['dead_feeds'].split(',')
            for pk in pks:
                feed = Feed.objects.get(pk=pk)
                feed.fetch_frequency = 0
                print 'killed %s' % feed.link
                print 'subscribers: %s' % feed.subscribers
                print
                feed.save()
