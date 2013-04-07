# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FlowModel'
        db.create_table(u'raven_flowmodel', (
            ('id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], primary_key=True)),
            ('flow', self.gf('oauth2client.django_orm.FlowField')(null=True)),
        ))
        db.send_create_signal(u'raven', ['FlowModel'])

        # Adding model 'CredentialsModel'
        db.create_table(u'raven_credentialsmodel', (
            ('id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], primary_key=True)),
            ('credential', self.gf('oauth2client.django_orm.CredentialsField')(null=True)),
        ))
        db.send_create_signal(u'raven', ['CredentialsModel'])

        # Adding model 'UserFeedItem'
        db.create_table(u'raven_userfeeditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['raven.FeedItem'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['auth.User'])),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'raven', ['UserFeedItem'])

        # Adding unique constraint on 'UserFeedItem', fields ['item', 'user']
        db.create_unique(u'raven_userfeeditem', ['item_id', 'user_id'])

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

        # Adding M2M table for field users on 'Feed'
        db.create_table(u'raven_feed_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feed', models.ForeignKey(orm[u'raven.feed'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'raven_feed_users', ['feed_id', 'user_id'])

        # Adding model 'FeedItem'
        db.create_table(u'raven_feeditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['raven.Feed'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('published', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'raven', ['FeedItem'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserFeedItem', fields ['item', 'user']
        db.delete_unique(u'raven_userfeeditem', ['item_id', 'user_id'])

        # Deleting model 'FlowModel'
        db.delete_table(u'raven_flowmodel')

        # Deleting model 'CredentialsModel'
        db.delete_table(u'raven_credentialsmodel')

        # Deleting model 'UserFeedItem'
        db.delete_table(u'raven_userfeeditem')

        # Deleting model 'Feed'
        db.delete_table(u'raven_feed')

        # Removing M2M table for field users on 'Feed'
        db.delete_table('raven_feed_users')

        # Deleting model 'FeedItem'
        db.delete_table(u'raven_feeditem')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'raven.credentialsmodel': {
            'Meta': {'object_name': 'CredentialsModel'},
            'credential': ('oauth2client.django_orm.CredentialsField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'primary_key': 'True'})
        },
        u'raven.feed': {
            'Meta': {'object_name': 'Feed'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'generator': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '500'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'feeds'", 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'raven.feeditem': {
            'Meta': {'object_name': 'FeedItem'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['raven.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '500'}),
            'published': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'raven.flowmodel': {
            'Meta': {'object_name': 'FlowModel'},
            'flow': ('oauth2client.django_orm.FlowField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'primary_key': 'True'})
        },
        u'raven.userfeeditem': {
            'Meta': {'unique_together': "(('item', 'user'),)", 'object_name': 'UserFeedItem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['raven.FeedItem']"}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['raven']
