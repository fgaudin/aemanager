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
from project.models import Proposal, Project
from accounts.models import Invoice
from contact.models import Contact, CONTACT_TYPE_COMPANY, Address
from autoentrepreneur.models import Subscription
from django.test.testcases import TransactionTestCase
from core.models import OwnedObject
from django.core.exceptions import SuspiciousOperation
from django.core import mail
from django.utils.translation import ugettext

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

    def test_backup(self):
        response = self.client.get(reverse('backup'))
        self.assertEquals(response.status_code, 200)

        response = self.client.post(reverse('backup'),
                                    {'backup_or_restore': 'backup'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.user1.backuprequest.state, BACKUP_RESTORE_STATE_PENDING)

        call_command('backup_user_data')

        self.assertEquals(BackupRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertTrue(os.path.exists('%s%s/backup/backup_%s.tar.gz' % (settings.FILE_UPLOAD_DIR,
                                                                         self.user1.get_profile().uuid,
                                                                         self.user1.backuprequest.creation_datetime.strftime('%Y%m%d%H%M'))))

    def test_restore_add_missing(self):
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

        self.assertTrue(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(pk=p.id).reference, 'modified')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 1)

    def test_restore_add_and_update(self):
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

        self.assertTrue(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(pk=p.id).reference, 'ref1')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 1)

    def test_restore_delete_all_and_restore(self):
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

        self.assertTrue(RestoreRequest.objects.get(user=self.user1).state, BACKUP_RESTORE_STATE_DONE)
        self.assertEquals(Proposal.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Proposal.objects.count(), 2)
        self.assertEquals(Proposal.objects.get(uuid=p.uuid).reference, 'ref1')

        self.assertEquals(Invoice.objects.count(), 2)
        self.assertEquals(Invoice.objects.filter(owner=self.user1).count(), 1)
        self.assertEquals(Invoice.objects.filter(owner=self.user1,
                                                 uuid=i.uuid).count(), 1)

        self.assertEquals(Contact.objects.filter(pk=c.id).count(), 0)

    def test_cannot_add_user(self):
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

    def test_cannot_update_subscription(self):
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
        self.assertEquals(Subscription.objects.filter(owner=self.user1)[0].state, 3)

    def test_cannot_reference_not_owned_object(self):
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

    def test_uuid_from_other_create_new_object(self):
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

    def test_tar_with_unneeded_files(self):
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

    def test_tar_trying_to_add_files_in_parent_directories(self):
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

    def test_dump_referencing_other_user_files(self):
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

    def test_username_injection(self):
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

    def test_backup_restore_backup_stability(self):
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
