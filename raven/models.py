from django.db import models


class Feed(models.Model):
    '''A model for representing an RSS feed.'''

    description = models.TextField()
    generator = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    url = models.URLField()
    # Disabled until we figure out auth.
    #user = models.ForeignKey(User)


class FeedItem(models.Model):
    '''A model for representing an item in a RSS feed.'''

    description = models.TextField()
    feed = models.ForeignKey(Feed, related_name='items')
    guid = models.CharField(max_length=500)
    published = models.DateTimeField()
    title = models.CharField(max_length=200)
    # It's possible to have longer urls, but anything longer than 2083
    # characters will break in IE.
    url = models.URLField(max_length=500)

