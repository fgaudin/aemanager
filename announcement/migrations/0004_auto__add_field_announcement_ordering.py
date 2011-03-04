# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Announcement.ordering'
        db.add_column('announcement_announcement', 'ordering', self.gf('django.db.models.fields.IntegerField')(default=1, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Announcement.ordering'
        db.delete_column('announcement_announcement', 'ordering')


    models = {
        'announcement.announcement': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Announcement'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'})
        }
    }

    complete_apps = ['announcement']
