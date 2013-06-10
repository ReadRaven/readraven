# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'UserFeedItem', fields ['feed', 'read', 'user', 'item']
        db.create_index(u'raven_userfeeditem', ['feed_id', 'read', 'user_id', 'item_id'])

        # Adding index on 'UserFeed', fields ['feed', 'user']
        db.create_index(u'raven_userfeed', ['feed_id', 'user_id'])

        # Adding index on 'FeedItem', fields ['feed', 'guid']
        db.create_index(u'raven_feeditem', ['feed_id', 'guid'])

        # Adding index on 'FeedItem', fields ['feed', 'published']
        db.create_index(u'raven_feeditem', ['feed_id', 'published'])


    def backwards(self, orm):
        # Removing index on 'FeedItem', fields ['feed', 'published']
        db.delete_index(u'raven_feeditem', ['feed_id', 'published'])

        # Removing index on 'FeedItem', fields ['feed', 'guid']
        db.delete_index(u'raven_feeditem', ['feed_id', 'guid'])

        # Removing index on 'UserFeed', fields ['feed', 'user']
        db.delete_index(u'raven_userfeed', ['feed_id', 'user_id'])

        # Removing index on 'UserFeedItem', fields ['feed', 'read', 'user', 'item']
        db.delete_index(u'raven_userfeeditem', ['feed_id', 'read', 'user_id', 'item_id'])


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'raven.feed': {
            'Meta': {'object_name': 'Feed'},
            'dead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'fetch_frequency': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'generator': ('django.db.models.fields.CharField', [], {'max_length': '1023', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '1023'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '1023', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1023'})
        },
        u'raven.feeditem': {
            'Meta': {'unique_together': "(('feed', 'guid'),)", 'object_name': 'FeedItem', 'index_together': "[['feed', 'guid'], ['feed', 'published']]"},
            'atom_id': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['raven.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '1023'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'reader_guid': ('django.db.models.fields.CharField', [], {'max_length': '48', 'unique': 'True', 'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        u'raven.userfeed': {
            'Meta': {'unique_together': "(('user', 'feed'),)", 'object_name': 'UserFeed', 'index_together': "[['user', 'feed']]"},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeds'", 'to': u"orm['raven.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeds'", 'to': u"orm['usher.User']"})
        },
        u'raven.userfeeditem': {
            'Meta': {'unique_together': "(('user', 'feed', 'item'),)", 'object_name': 'UserFeedItem', 'index_together': "[['user', 'feed', 'read', 'item']]"},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feeditems'", 'to': u"orm['raven.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeditems'", 'to': u"orm['raven.FeedItem']"}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'starred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeditems'", 'to': u"orm['usher.User']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        },
        u'usher.user': {
            'Meta': {'object_name': 'User'},
            'credential': ('oauth2client.django_orm.CredentialsField', [], {'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '254', 'db_index': 'True'}),
            'flow': ('oauth2client.django_orm.FlowField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'sync_task_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '254'})
        }
    }

    complete_apps = ['raven']