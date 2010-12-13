# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Country'
        db.create_table('contact_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country_code2', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('country_code3', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('country_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('contact', ['Country'])

        # Adding model 'Address'
        db.create_table('contact_address', (
            ('ownedobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.OwnedObject'], unique=True, primary_key=True)),
            ('street', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('zipcode', self.gf('django.db.models.fields.CharField')(default='', max_length=10, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Country'], null=True, blank=True)),
        ))
        db.send_create_signal('contact', ['Address'])

        # Adding model 'Contact'
        db.create_table('contact_contact', (
            ('ownedobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.OwnedObject'], unique=True, primary_key=True)),
            ('contact_type', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('firstname', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('function', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True)),
            ('company_id', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True)),
            ('legal_form', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('representative', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('representative_function', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(default='', max_length=75, blank=True)),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Address'])),
        ))
        db.send_create_signal('contact', ['Contact'])

        # Adding M2M table for field contacts on 'Contact'
        db.create_table('contact_contact_contacts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_contact', models.ForeignKey(orm['contact.contact'], null=False)),
            ('to_contact', models.ForeignKey(orm['contact.contact'], null=False))
        ))
        db.create_unique('contact_contact_contacts', ['from_contact_id', 'to_contact_id'])

        # Adding model 'PhoneNumber'
        db.create_table('contact_phonenumber', (
            ('ownedobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.OwnedObject'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contact.Contact'])),
        ))
        db.send_create_signal('contact', ['PhoneNumber'])


    def backwards(self, orm):
        
        # Deleting model 'Country'
        db.delete_table('contact_country')

        # Deleting model 'Address'
        db.delete_table('contact_address')

        # Deleting model 'Contact'
        db.delete_table('contact_contact')

        # Removing M2M table for field contacts on 'Contact'
        db.delete_table('contact_contact_contacts')

        # Deleting model 'PhoneNumber'
        db.delete_table('contact_phonenumber')


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
        'contact.address': {
            'Meta': {'object_name': 'Address', '_ormbases': ['core.OwnedObject']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Country']", 'null': 'True', 'blank': 'True'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'street': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'})
        },
        'contact.contact': {
            'Meta': {'object_name': 'Contact', '_ormbases': ['core.OwnedObject']},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Address']"}),
            'company_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'contact_type': ('django.db.models.fields.IntegerField', [], {}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['contact.Contact']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'blank': 'True'}),
            'firstname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'function': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'legal_form': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'representative': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'representative_function': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'})
        },
        'contact.country': {
            'Meta': {'ordering': "['country_name']", 'object_name': 'Country'},
            'country_code2': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'country_code3': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'country_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contact.phonenumber': {
            'Meta': {'object_name': 'PhoneNumber', '_ormbases': ['core.OwnedObject']},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
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

    complete_apps = ['contact']
