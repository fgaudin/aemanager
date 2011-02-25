# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'Announcement', fields ['enabled']
        db.create_index('announcement_announcement', ['enabled'])


    def backwards(self, orm):
        
        # Removing index on 'Announcement', fields ['enabled']
        db.delete_index('announcement_announcement', ['enabled'])


    models = {
        'announcement.announcement': {
            'Meta': {'object_name': 'Announcement'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['announcement']
