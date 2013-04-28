# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserFeed'
        db.create_table(u'raven_userfeed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userfeeds', to=orm['raven.Feed'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userfeeds', to=orm['usher.User'])),
        ))
        db.send_create_signal(u'raven', ['UserFeed'])

        # Adding unique constraint on 'UserFeed', fields ['user', 'feed']
        db.create_unique(u'raven_userfeed', ['user_id', 'feed_id'])

        # Adding model 'UserFeedItem'
        db.create_table(u'raven_userfeeditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userfeeditems', to=orm['raven.FeedItem'])),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='feeditems', to=orm['raven.Feed'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userfeeditems', to=orm['usher.User'])),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'raven', ['UserFeedItem'])

        # Adding unique constraint on 'UserFeedItem', fields ['user', 'item']
        db.create_unique(u'raven_userfeeditem', ['user_id', 'item_id'])

        # Adding model 'Feed'
        db.create_table(u'raven_feed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_fetched', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('generator', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'raven', ['Feed'])

        # Adding model 'FeedItem'
        db.create_table(u'raven_feeditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['raven.Feed'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('published', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal(u'raven', ['FeedItem'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserFeedItem', fields ['user', 'item']
        db.delete_unique(u'raven_userfeeditem', ['user_id', 'item_id'])

        # Removing unique constraint on 'UserFeed', fields ['user', 'feed']
        db.delete_unique(u'raven_userfeed', ['user_id', 'feed_id'])

        # Deleting model 'UserFeed'
        db.delete_table(u'raven_userfeed')

        # Deleting model 'UserFeedItem'
        db.delete_table(u'raven_userfeeditem')

        # Deleting model 'Feed'
        db.delete_table(u'raven_feed')

        # Deleting model 'FeedItem'
        db.delete_table(u'raven_feeditem')


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
            'generator': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '500'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'raven.feeditem': {
            'Meta': {'object_name': 'FeedItem'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['raven.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '500'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'raven.userfeed': {
            'Meta': {'unique_together': "(('user', 'feed'),)", 'object_name': 'UserFeed'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeds'", 'to': u"orm['raven.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeds'", 'to': u"orm['usher.User']"})
        },
        u'raven.userfeeditem': {
            'Meta': {'unique_together': "(('user', 'item'),)", 'object_name': 'UserFeedItem'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'feeditems'", 'to': u"orm['raven.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userfeeditems'", 'to': u"orm['raven.FeedItem']"}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'username': ('django.db.models.fields.CharField', [], {'max_length': '254'})
        }
    }

    complete_apps = ['raven']