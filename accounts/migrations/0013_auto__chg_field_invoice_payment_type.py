# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Invoice.payment_type'
        db.alter_column('accounts_invoice', 'payment_type', self.gf('django.db.models.fields.IntegerField')(null=True))


    def backwards(self, orm):

        # Changing field 'Invoice.payment_type'
        db.alter_column('accounts_invoice', 'payment_type', self.gf('django.db.models.fields.IntegerField')(default=1))


    models = {
        'accounts.expense': {
            'Meta': {'object_name': 'Expense', '_ormbases': ['core.OwnedObject']},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'payment_type': ('django.db.models.fields.IntegerField', [], {}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'supplier': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'})
        },
        'accounts.invoice': {
            'Meta': {'ordering': "['invoice_id']", 'object_name': 'Invoice', '_ormbases': ['core.OwnedObject']},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']", 'null': 'True', 'blank': 'True'}),
            'discount_conditions': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'edition_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'execution_begin_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'execution_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'invoice_id': ('django.db.models.fields.IntegerField', [], {}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'paid_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'payment_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'payment_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'penalty_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'penalty_rate': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'})
        },
        'accounts.invoicerow': {
            'Meta': {'ordering': "['id']", 'object_name': 'InvoiceRow'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'balance_payments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'category': ('django.db.models.fields.IntegerField', [], {}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoice_rows'", 'to': "orm['accounts.Invoice']"}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'proposal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoice_rows'", 'to': "orm['project.Proposal']"}),
            'quantity': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '1'}),
            'unit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'})
        },
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
            'comment': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'company_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'contact_type': ('django.db.models.fields.IntegerField', [], {}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'contacts_rel_+'", 'null': 'True', 'to': "orm['contact.Contact']"}),
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
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '36'})
        },
        'project.project': {
            'Meta': {'object_name': 'Project', '_ormbases': ['core.OwnedObject']},
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contact.Contact']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'})
        },
        'project.proposal': {
            'Meta': {'ordering': "['begin_date', 'update_date']", 'object_name': 'Proposal', '_ormbases': ['core.OwnedObject']},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'begin_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'contract_content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'contract_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'ownedobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.OwnedObject']", 'unique': 'True', 'primary_key': 'True'}),
            'payment_delay': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'payment_delay_other': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'payment_delay_type_other': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['project.Project']"}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'}),
            'update_date': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['accounts']
