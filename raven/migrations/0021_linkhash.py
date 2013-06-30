# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        # http://stackoverflow.com/questions/3314173/how-to-call-a-static-methods-on-a-django-model-class-during-a-south-migration
        import hashlib
        for item in orm['raven.FeedItem'].objects.all():
            link_hash = hashlib.sha256()
            link_hash.update(item.link.encode('utf-8'))
            item.link_hash = link_hash.hexdigest()
            item.save()

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

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
            'description': ('django.db.models.fields.TextField', [], {}),
            'fetch_frequency': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'generator': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'site': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feed'", 'null': 'True', 'to': u"orm['subscriber.Subscription']"}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        u'raven.feeditem': {
            'Meta': {'unique_together': "(('feed', 'guid'),)", 'object_name': 'FeedItem', 'index_together': "[['feed', 'guid'], ['feed', 'link'], ['feed', 'title'], ['feed', 'atom_id'], ['feed', 'published']]"},
            'atom_id': ('django.db.models.fields.TextField', [], {'default': "''", 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['raven.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '1023'}),
            'link_hash': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'db_index': 'True'}),
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
        u'subscriber.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'hub': ('django.db.models.fields.URLField', [], {'max_length': '1023'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lease_expiration': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'topic': ('django.db.models.fields.URLField', [], {'max_length': '1023'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verify_token': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
    symmetrical = True
