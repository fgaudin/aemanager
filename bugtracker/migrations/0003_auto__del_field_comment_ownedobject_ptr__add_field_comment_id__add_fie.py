# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Deleting field 'Comment.ownedobject_ptr'
        db.delete_column('bugtracker_comment', 'ownedobject_ptr_id')

        # Adding field 'Comment.id'
        db.add_column('bugtracker_comment', 'id', self.gf('django.db.models.fields.AutoField')(default=1, primary_key=True), keep_default=False)

        # Adding field 'Comment.owner'
        db.add_column('bugtracker_comment', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True), keep_default=False)

        # Deleting field 'Issue.ownedobject_ptr'
        db.delete_column('bugtracker_issue', 'ownedobject_ptr_id')

        # Adding field 'Issue.id'
        db.add_column('bugtracker_issue', 'id', self.gf('django.db.models.fields.AutoField')(default=1, primary_key=True), keep_default=False)

        # Adding field 'Issue.owner'
        db.add_column('bugtracker_issue', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True), keep_default=False)

        # Deleting field 'Vote.user'
        db.delete_column('bugtracker_vote', 'user_id')

        # Adding field 'Vote.owner'
        db.add_column('bugtracker_vote', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['auth.User']), keep_default=False)


    def backwards(self, orm):

        # We cannot add back in field 'Comment.ownedobject_ptr'
        raise RuntimeError(
            "Cannot reverse this migration. 'Comment.ownedobject_ptr' and its values cannot be restored.")

        # Deleting field 'Comment.id'
        db.delete_column('bugtracker_comment', 'id')

        # Deleting field 'Comment.owner'
        db.delete_column('bugtracker_comment', 'owner_id')

        # We cannot add back in field 'Issue.ownedobject_ptr'
        raise RuntimeError(
            "Cannot reverse this migration. 'Issue.ownedobject_ptr' and its values cannot be restored.")

        # Deleting field 'Issue.id'
        db.delete_column('bugtracker_issue', 'id')

        # Deleting field 'Issue.owner'
        db.delete_column('bugtracker_issue', 'owner_id')

        # We cannot add back in field 'Vote.user'
        raise RuntimeError(
            "Cannot reverse this migration. 'Vote.user' and its values cannot be restored.")

        # Deleting field 'Vote.owner'
        db.delete_column('bugtracker_vote', 'owner_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'bugtracker.comment': {
            'Meta': {'ordering': "['update_date']", 'object_name': 'Comment'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bugtracker.Issue']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'bugtracker.issue': {
            'Meta': {'object_name': 'Issue'},
            'category': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'bugtracker.vote': {
            'Meta': {'object_name': 'Vote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bugtracker.Issue']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['bugtracker']
