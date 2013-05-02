# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.sync_task_id'
        db.add_column(u'usher_user', 'sync_task_id',
                      self.gf('django.db.models.fields.CharField')(max_length=255, unique=True, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.sync_task_id'
        db.delete_column(u'usher_user', 'sync_task_id')


    models = {
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

    complete_apps = ['usher']