from backup.models import BackupRequest, BACKUP_RESTORE_STATE_PENDING, \
    BACKUP_RESTORE_STATE_DONE, RESTORE_ACTION_ADD_MISSING, \
    RestoreRequest, RESTORE_ACTION_ADD_AND_UPDATE, \
    RESTORE_ACTION_DELETE_ALL_AND_RESTORE, BACKUP_RESTORE_STATE_ERROR
from django.contrib.auth.models import User
import hashlib
import tarfile
import shutil
from django.core.urlresolvers import reverse
import os
from django.conf import settings
from django.core.management import call_command
from project.models import Proposal, Project, PROPOSAL_STATE_ACCEPTED, \
    ROW_CATEGORY_SERVICE, VAT_RATES_19_6
from accounts.models import Invoice, INVOICE_STATE_PAID, PAYMENT_TYPE_CHECK, \
    PAYMENT_TYPE_BANK_CARD, INVOICE_STATE_EDITED, InvoiceRow
from contact.models import Contact, CONTACT_TYPE_COMPANY, Address
from autoentrepreneur.models import Subscription, SUBSCRIPTION_STATE_TRIAL
from django.test.testcases import TransactionTestCase, TestCase
from core.models import OwnedObject
from django.core.exceptions import SuspiciousOperation
from django.core import mail
from django.utils.translation import ugettext
import datetime

class BackupTest(TransactionTestCase):
    fixtures = ['backup_data']

    def setUp(self):
        if os.path.exists(settings.FILE_UPLOAD_DIR):
            shutil.move(settings.FILE_UPLOAD_DIR[:-1], '%s_backup' % (settings.FILE_UPLOAD_DIR[:-1]))

        shutil.copytree('%s/backup/fixtures/uploaded_files' % (settings.BASE_PATH),
                        settings.FILE_UPLOAD_DIR[:-1])

        self.user1 = User.objects.get(username='test1')
        self.user2 = User.objects.get(username='test2')
        self.client.login(username='test1', password='test')

    def tearDown(self):
        if os.path.exists(settings.FILE_UPLOAD_DIR):
            shutil.rmtree(settings.FILE_UPLOAD_DIR[:-1])
        if os.path.exists('%s_backup' % (settings.FILE_UPLOAD_DIR[:-1])):
            shutil.move('%s_backup' % (settings.FILE_UPLOAD_DIR[:-1]), settings.FILE_UPLOAD_DIR[:-1])

    def testBackup(self):
        response = self.client.get(reverse('backup'))
        self.assertEquals(response.status_code, 200)

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.backuprequest.state, BACKUP_RESTORE_STATE_PENDING)

        call_command('backup_user_data')

        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)

        filename = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                     self.user1.get_profile().uuid,
                                                     self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        self.assertTrue(os.path.exists(filename))
        self.assertNotEquals(os.path.getsize(filename), 0)

    def testRestoreAddMissing(self):
        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        call_command('backup_user_data')

        # modify an object -> shouldn't be updated after restore
        p = Proposal.objects.get(owner=self.user1)
        p.reference = 'modified'
        p.save()

        # delete an object -> should be restored
        i = Invoice.objects.get(owner=self.user1)
        i.delete()

        # add an object -> souldn't be modified after restore
        a = Address.objects.create(street='2 rue de la paix',
                                   zipcode='75002',
                                   city='Paris',
                                   owner=self.user1)
        c = Contact.objects.create(contact_type=CONTACT_TYPE_COMPANY,
                                   name='New contact',
                                   company_id='456',
                                   legal_form='SA',
                                   representative='Roger',
                                   representative_function='President',
                                   address=a,
                                   comment='new comment',
                                   owner=self.user1)

        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_ADD_MISSING,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_%s.tar.gz' % (self.user1.get_profile().uuid,
                                                           self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M')))
        shutil.copyfile(backup_file, restore_file)

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(pk=p.id).reference, 'modified')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 1)

    def testRestoreAddAndUpdate(self):
        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        call_command('backup_user_data')

        # modify an object -> shouldn't be updated after restore
        p = Proposal.objects.get(owner=self.user1)
        p.reference = 'modified'
        p.save()

        # delete an object -> should be restored
        i = Invoice.objects.get(owner=self.user1)
        i.delete()

        # add an object -> souldn't be modified after restore
        a = Address.objects.create(street='2 rue de la paix',
                                   zipcode='75002',
                                   city='Paris',
                                   owner=self.user1)
        c = Contact.objects.create(contact_type=CONTACT_TYPE_COMPANY,
                                   name='New contact',
                                   company_id='456',
                                   legal_form='SA',
                                   representative='Roger',
                                   representative_function='President',
                                   address=a,
                                   comment='new comment',
                                   owner=self.user1)

        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_ADD_AND_UPDATE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_%s.tar.gz' % (self.user1.get_profile().uuid,
                                                           self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M')))
        shutil.copyfile(backup_file, restore_file)

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(pk=p.id).reference, 'ref1')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 1)

    def testRestoreDeleteAllAndRestore(self):
        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        call_command('backup_user_data')

        # modify an object -> shouldn't be updated after restore
        p = Proposal.objects.get(owner=self.user1)
        p.reference = 'modified'
        p.save()

        # delete an object -> should be restored
        i = Invoice.objects.get(owner=self.user1)
        i.delete()

        # add an object -> souldn't be modified after restore
        a = Address.objects.create(street='2 rue de la paix',
                                   zipcode='75002',
                                   city='Paris',
                                   owner=self.user1)
        c = Contact.objects.create(contact_type=CONTACT_TYPE_COMPANY,
                                   name='New contact',
                                   company_id='456',
                                   legal_form='SA',
                                   representative='Roger',
                                   representative_function='President',
                                   address=a,
                                   comment='new comment',
                                   owner=self.user1)

        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_%s.tar.gz' % (self.user1.get_profile().uuid,
                                                           self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M')))
        shutil.copyfile(backup_file, restore_file)

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(uuid=p.uuid).reference, 'ref1')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 0)

    def testCannotAddUser(self):
        backup_file = '%s/backup/fixtures/backup_injected_user.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_injected_user.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                     self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_injected_user.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(User.objects.count(), 2)

    def testCannotUpdateSubscription(self):
        backup_file = '%s/backup/fixtures/backup_injected_subscription.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_injected_subscription.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                             self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_injected_subscription.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(Subscription.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Subscription.objects.filter(owner=self.user1)[0].state, 2)

    def testCannotReferenceNotOwnedObject(self):
        backup_file = '%s/backup/fixtures/backup_with_disallowed_reference.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_with_disallowed_reference.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                                 self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_with_disallowed_reference.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))
        self.assertEquals(Project.objects.filter(owner=self.user1).count(), 1)

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_ERROR)
        self.assertEquals(RestoreRequest.objects.get(user=self.user1).error_message, 'Reference to a missing object')
        self.assertEquals(Project.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Project.objects.get(owner=self.user1).customer.uuid, 'b433886f-3505-43f9-8274-4193a6c9758c')
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, ugettext("%sRestore failed") % (settings.EMAIL_SUBJECT_PREFIX))

    def testUuidFromOtherCreateNewObject(self):
        backup_file = '%s/backup/fixtures/backup_from_other_user.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_from_other_user.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                       self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_from_other_user.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))
        self.assertEquals(Project.objects.filter(owner=self.user1).count(), 1)

        call_command('restore_user_data')

        self.assertEquals(OwnedObject.objects.filter(owner=self.user2).count(), 12)

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertNotEquals(Project.objects.get(owner=self.user1).customer.uuid, 'fa73c0f1-1abc-4b60-a6a6-42b7dea8e989')
        self.assertEquals(Project.objects.get(owner=self.user1).customer.owner, self.user1)

    def testTarWithUnneededFiles(self):
        """
        with files that won't be restored
        """
        backup_file = '%s/backup/fixtures/backup_injected_files.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_injected_files.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                      self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_injected_files.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)

        self.assertEquals(set(os.listdir('%s%s' % (settings.FILE_UPLOAD_DIR, self.user1.get_profile().uuid))),
                              set([u'proposal', u'restore', u'contract', u'logo']))

    def testTarTryingToAddFilesInParentDirectories(self):
        backup_file = '%s/backup/fixtures/backup_dest_dir_modified.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_dest_dir_modified.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                         self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_dest_dir_modified.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertFalse(os.path.exists('%s/restore/injected_file.txt' % (self.user1.get_profile().uuid)))
        self.assertFalse(os.path.exists('%s/injected_file.txt' % (self.user1.get_profile().uuid)))
        self.assertFalse(os.path.exists('%s/../injected_file.txt' % (self.user1.get_profile().uuid)))

    def testDumpReferencingOtherUserFiles(self):
        backup_file = '%s/backup/fixtures/backup_referencing_other_files.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_referencing_other_files.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                               self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_referencing_other_files.tar.gz' % (self.user1.get_profile().uuid))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.get(uuid='2e6bed41-43e5-41b1-8c7f-60353e7727a2').contract_file.name,
                          '%s/proposal/contract.pdf' % (self.user1.get_profile().uuid))

    def testUsernameInjection(self):
        """
        injected username can't pass through upload dir restriction
        """
        profile = self.user1.get_profile()
        profile.uuid = '../injected_user'
        profile.save()

        backup_file = '%s/backup/fixtures/backup_normal.tar.gz' % (settings.BASE_PATH)
        restore_file = '%s%s/restore/backup_normal.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                              self.user1.get_profile().uuid)

        self.assertTrue(os.path.exists(backup_file))

        self.assertRaises(SuspiciousOperation,
                          self.client.post,
                          reverse('backup'),
                          {'backup_or_restore': 'restore',
                           'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                           'backup_file': open(backup_file, 'rb')})

    def testBackupRestoreBackupStability(self):
        """
        verify that a backup, restore with delete and backup give the
        same backup file
        """
        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.backuprequest.state, BACKUP_RESTORE_STATE_PENDING)

        call_command('backup_user_data')

        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        self.assertTrue(os.path.exists(backup_file))

        backup = tarfile.open(backup_file, 'r:gz')
        backup_file_md5 = hashlib.md5()
        for member in backup:
            if member.isfile():
                file = backup.extractfile(member)
                backup_file_md5.update(file.read())
        backup_digest = backup_file_md5.hexdigest()

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_%s.tar.gz' % (self.user1.get_profile().uuid,
                                                           self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M')))
        shutil.copyfile(backup_file, restore_file)
        self.assertTrue(os.path.exists(restore_file))

        call_command('restore_user_data')

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_PENDING)

        call_command('backup_user_data')

        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        new_backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                            self.user1.get_profile().uuid,
                                                            BackupRequest.objects.get(user=self.user1).creation_datetime.strftime('%Y%m%d%H%M'))

        new_backup = tarfile.open(new_backup_file, 'r:gz')
        new_backup_file_md5 = hashlib.md5()
        for member in new_backup:
            if member.isfile():
                file = new_backup.extractfile(member)
                new_backup_file_md5.update(file.read())
        new_backup_digest = new_backup_file_md5.hexdigest()

        self.assertEquals(backup_digest, new_backup_digest)

    def testCantRestoreIfTrial(self):
        sub = Subscription.objects.get(owner__username='test1')
        sub.state = SUBSCRIPTION_STATE_TRIAL
        sub.save()

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        call_command('backup_user_data')

        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_DELETE_ALL_AND_RESTORE,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertContains(response, 'You have to subscribe to restore your backups', status_code=200)

    def testBackupWithNoProposalAndNoVat(self):
        profile = self.user1.get_profile()
        profile.vat_number = '1234'
        profile.save()

        customer = Contact.objects.all()[0]
        i = Invoice.objects.create(customer=customer,
                                   invoice_id=10,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner=self.user1)

        i_row = InvoiceRow.objects.create(proposal=None,
                                          vat_rate=None,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=5,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner=self.user1)

        i_row = InvoiceRow.objects.create(proposal=None,
                                          vat_rate=VAT_RATES_19_6,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=5,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner=self.user1)

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.backuprequest.state, BACKUP_RESTORE_STATE_PENDING)

        call_command('backup_user_data')

        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)

        filename = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                     self.user1.get_profile().uuid,
                                                     self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        self.assertTrue(os.path.exists(filename))
        self.assertNotEquals(os.path.getsize(filename), 0)

    def testRestoreWithNoProposalAndNoVat(self):
        profile = self.user1.get_profile()
        profile.vat_number = '1234'
        profile.save()

        customer = Contact.objects.filter(owner=self.user1)[0]
        i = Invoice.objects.create(customer=customer,
                                   invoice_id=10,
                                   state=INVOICE_STATE_EDITED,
                                   amount='1000',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=None,
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner=self.user1)

        i_row = InvoiceRow.objects.create(proposal=None,
                                          vat_rate=None,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=5,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner=self.user1)

        i_row = InvoiceRow.objects.create(proposal=None,
                                          vat_rate=VAT_RATES_19_6,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=5,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner=self.user1)

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        call_command('backup_user_data')

        # delete the new invoice
        invoice_uuid = i.uuid
        i.delete()

        backup_file = '%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                        self.user1.get_profile().uuid,
                                                        self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))
        restore_file = '%s%s/restore/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                          self.user1.get_profile().uuid,
                                                          self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'restore',
                                     'action': RESTORE_ACTION_ADD_MISSING,
                                     'backup_file': open(backup_file, 'rb')})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.restorerequest.state, BACKUP_RESTORE_STATE_PENDING)
        self.assertEquals(self.user1.restorerequest.backup_file.name,
                          '%s/restore/backup_%s.tar.gz' % (self.user1.get_profile().uuid,
                                                           self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M')))
        shutil.copyfile(backup_file, restore_file)

        call_command('restore_user_data')

        self.assertEquals(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)

        self.assertEquals(Invoice.objects.count(), 3)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=invoice_uuid).count(), 1)

        self.assertEquals(InvoiceRow.objects.filter(invoice__uuid=invoice_uuid, proposal=None, vat_rate=None).count(), 1)
        self.assertEquals(InvoiceRow.objects.filter(invoice__uuid=invoice_uuid, proposal=None, vat_rate=VAT_RATES_19_6).count(), 1)

class CsvExportTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.proposal1 = Proposal.objects.create(project_id=30,
                                                reference='crt1234',
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_ACCEPTED,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=2005,
                                                owner_id=1)

        self.invoice1_1 = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                                 invoice_id=1,
                                                 state=INVOICE_STATE_PAID,
                                                 amount='100',
                                                 edition_date=datetime.date(2010, 8, 31),
                                                 payment_date=datetime.date(2010, 9, 30),
                                                 paid_date=None,
                                                 payment_type=PAYMENT_TYPE_CHECK,
                                                 execution_begin_date=datetime.date(2010, 8, 1),
                                                 execution_end_date=datetime.date(2010, 8, 7),
                                                 penalty_date=datetime.date(2010, 10, 8),
                                                 penalty_rate='1.5',
                                                 discount_conditions='Nothing',
                                                 owner_id=1)

        self.proposal2 = Proposal.objects.create(project_id=30,
                                                 reference='crt1234',
                                                 update_date=datetime.date.today(),
                                                 state=PROPOSAL_STATE_ACCEPTED,
                                                 begin_date=datetime.date(2010, 8, 1),
                                                 end_date=datetime.date(2010, 8, 15),
                                                 contract_content='Content of contract',
                                                 amount=2005,
                                                 owner_id=2)

        self.invoice2_1 = Invoice.objects.create(customer_id=self.proposal2.project.customer_id,
                                                 invoice_id=2,
                                                 state=INVOICE_STATE_PAID,
                                                 amount='200',
                                                 edition_date=datetime.date(2010, 4, 5),
                                                 payment_date=datetime.date(2010, 5, 10),
                                                 paid_date=None,
                                                 payment_type=PAYMENT_TYPE_BANK_CARD,
                                                 execution_begin_date=datetime.date(2010, 3, 2),
                                                 execution_end_date=datetime.date(2010, 3, 9),
                                                 penalty_date=datetime.date(2010, 9, 8),
                                                 penalty_rate='2.5',
                                                 discount_conditions='20%',
                                                 owner_id=2)

    def testExport(self):
        response = self.client.get(reverse('csv_export'))
        expected_response = "Reference,Customer,Address,State,Amount,Edition date,Payment date,Payment type,Paid date,Execution begin date,Execution end date,Penalty date,Penalty rate,Discount conditions\r\n1,Contact 1,\",  , None\",Paid,100.00,2010-08-31,2010-09-30,Check,None,2010-08-01,2010-08-07,2010-10-08,1.50,Nothing\r\n"
        self.assertEquals(response.content, expected_response)

    def testExportDate(self):
        invoice1_2 = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                            invoice_id=2,
                                            state=INVOICE_STATE_PAID,
                                            amount='200',
                                            edition_date=datetime.date(2010, 1, 31),
                                            payment_date=datetime.date(2010, 2, 28),
                                            paid_date=None,
                                            payment_type=PAYMENT_TYPE_CHECK,
                                            execution_begin_date=datetime.date(2010, 1, 1),
                                            execution_end_date=datetime.date(2010, 1, 7),
                                            penalty_date=datetime.date(2010, 3, 8),
                                            penalty_rate='1.5',
                                            discount_conditions='Nothing',
                                            owner_id=1)

        response = self.client.get(reverse('csv_export'),
                                   {'begin_date': datetime.date(2010, 1, 1)})
        expected_response = "Reference,Customer,Address,State,Amount,Edition date,Payment date,Payment type,Paid date,Execution begin date,Execution end date,Penalty date,Penalty rate,Discount conditions\r\n1,Contact 1,\",  , None\",Paid,100.00,2010-08-31,2010-09-30,Check,None,2010-08-01,2010-08-07,2010-10-08,1.50,Nothing\r\n2,Contact 1,\",  , None\",Paid,200.00,2010-01-31,2010-02-28,Check,None,2010-01-01,2010-01-07,2010-03-08,1.50,Nothing\r\n"
        self.assertEquals(response.content, expected_response)

        response = self.client.get(reverse('csv_export'),
                                   {'begin_date': datetime.date(2010, 2, 1)})
        expected_response = "Reference,Customer,Address,State,Amount,Edition date,Payment date,Payment type,Paid date,Execution begin date,Execution end date,Penalty date,Penalty rate,Discount conditions\r\n1,Contact 1,\",  , None\",Paid,100.00,2010-08-31,2010-09-30,Check,None,2010-08-01,2010-08-07,2010-10-08,1.50,Nothing\r\n"
        self.assertEquals(response.content, expected_response)

        response = self.client.get(reverse('csv_export'),
                                   {'end_date': datetime.date(2010, 2, 1)})
        expected_response = "Reference,Customer,Address,State,Amount,Edition date,Payment date,Payment type,Paid date,Execution begin date,Execution end date,Penalty date,Penalty rate,Discount conditions\r\n2,Contact 1,\",  , None\",Paid,200.00,2010-01-31,2010-02-28,Check,None,2010-01-01,2010-01-07,2010-03-08,1.50,Nothing\r\n"
        self.assertEquals(response.content, expected_response)
