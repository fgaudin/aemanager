# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("core", "0001_initial"),
    )

    def forwards(self, orm):

        # Adding model 'UserProfile'
        db.create_table('autoentrepreneur_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('company_name', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('company_id', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True)),
            ('bank_information', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Address'])),
            ('activity', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('creation_help', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('freeing_tax_payment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('payment_option', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('autoentrepreneur', ['UserProfile'])


    def backwards(self, orm):

        # Deleting model 'UserProfile'
        db.delete_table('autoentrepreneur_userprofile')


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
        'autoentrepreneur.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'activity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Address']"}),
            'bank_information': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'company_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'creation_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'freeing_tax_payment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_option': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'contact.address': {
            'Meta': {'object_name': 'Address', '_ormbases': ['core.OwnedObject']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Country']", 'null': 'True', 'blank': 'True'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'street': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'})
        },
        'contact.country': {
            'Meta': {'ordering': "['country_name']", 'object_name': 'Country'},
            'country_code2': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'country_code3': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'country_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.ownedobject': {
            'Meta': {'object_name': 'OwnedObject'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['autoentrepreneur']
