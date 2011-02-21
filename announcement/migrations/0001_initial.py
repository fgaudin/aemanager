# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Announcement'
        db.create_table('announcement_announcement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('announcement', ['Announcement'])


    def backwards(self, orm):
        
        # Deleting model 'Announcement'
        db.delete_table('announcement_announcement')


    models = {
        'announcement.announcement': {
            'Meta': {'object_name': 'Announcement'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['announcement']
