from django.contrib.auth.models import User
from django.db import models


class Feed(models.Model):
    '''A model for representing an RSS feed.'''

    user = models.ForeignKey(User)

    # Required properties
    description = models.TextField()
    link = models.URLField(max_length=500)
    title = models.CharField(max_length=200)

    # Optional metadata
    generator = models.CharField(max_length=100, blank=True)

    # Currently unused RSS (optional) properties:
    # category: <category>Filthy pornography</category>
    # cloud: <cloud domain="www...com" port="80" path="/RPC" registerProcedure="NotifyMe" protocol="xml-rpc">
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

    description = models.TextField()
    feed = models.ForeignKey(Feed, related_name='items')
    guid = models.CharField(max_length=500)
    published = models.DateTimeField()
    title = models.CharField(max_length=200)
    # It's possible to have longer urls, but anything longer than 2083
    # characters will break in IE.
    url = models.URLField(max_length=500)

