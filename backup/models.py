import uuid
import datetime
import shutil
import tarfile
import gzip

from xml.dom import pulldom
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from contact.models import Contact, PhoneNumber, Address, Country
from core.models import OwnedObject
from project.models import Contract, Project, Proposal, ProposalRow
from accounts.models import Invoice, InvoiceRow, Expense
import unicodedata
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from core.context_processors import version
from django.db.models.fields.related import ForeignKey, OneToOneField
import os
import errno
from django.core.serializers.xml_serializer import getInnerText
from django.core.mail import mail_admins

BACKUP_RESTORE_STATE_PENDING = 1
BACKUP_RESTORE_STATE_IN_PROGRESS = 2
BACKUP_RESTORE_STATE_DONE = 3
BACKUP_RESTORE_STATE_ERROR = 4
BACKUP_RESTORE_STATE = ((BACKUP_RESTORE_STATE_PENDING, _('Pending')),
                        (BACKUP_RESTORE_STATE_IN_PROGRESS, _('In progress')),
                        (BACKUP_RESTORE_STATE_DONE, _('Done')),
                        (BACKUP_RESTORE_STATE_ERROR, _('Error')))

def mkdir_p(dir):
    try:
        os.makedirs(dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

class BackupRequest(models.Model):
    user = models.OneToOneField(User)
    state = models.IntegerField(choices=BACKUP_RESTORE_STATE, default=BACKUP_RESTORE_STATE_PENDING)
    creation_datetime = models.DateTimeField()
    last_state_datetime = models.DateTimeField()
    error_message = models.CharField(max_length=255, null=True, blank=True)

    def is_done(self):
        return self.state == BACKUP_RESTORE_STATE_DONE

    def get_backup_filename(self):
        return 'backup_%s.tar.gz' % (self.creation_datetime.strftime('%Y%m%d%H%M'))

    def backup(self):

        class BackupTarInfo(tarfile.TarInfo):
            def setNothing(self, value):
                pass

            def getUid(self):
                return 10000

            def getGid(self):
                return 1000

            def getUname(self):
                return 'aemanager'

            def getGname(self):
                return 'aemanager'

            uid = property(getUid, setNothing)
            gid = property(getGid, setNothing)
            uname = property(getUname, setNothing)
            gname = property(getGname, setNothing)

        self.state = BACKUP_RESTORE_STATE_IN_PROGRESS
        self.last_state_datetime = datetime.datetime.now()
        self.save()

        self.backup_dir = '%s%s/backup/backup_%s' % (settings.FILE_UPLOAD_DIR,
                                                     self.user.get_profile().uuid,
                                                     self.creation_datetime.strftime('%Y%m%d%H%M'))
        try:
            # delete previous export dir
            shutil.rmtree('%s%s/backup' % (settings.FILE_UPLOAD_DIR,
                                           self.user.get_profile().uuid),
                                           True)

            # create export dir
            mkdir_p(self.backup_dir)

            # backup objects
            self.stream = open("%s/data.xml" % (self.backup_dir), 'w')
            self.backup_objects()
            self.stream.close()

            # backup files
            self.backup_files()

            # create the archive
            file = gzip.GzipFile('%s.tar.gz' % (self.backup_dir), 'w')
            tar = tarfile.TarFile(mode='w', fileobj=file, tarinfo=BackupTarInfo)
            tar.add(self.backup_dir, 'backup')
            tar.close()
            file.close()

            self.state = BACKUP_RESTORE_STATE_DONE
        except Exception as e:
            self.state = BACKUP_RESTORE_STATE_ERROR
            self.error_message = unicode(e)
            mail_subject = _('Backup failed')
            mail_message = _('Backup for %(user)s failed with message : %(message)s') % {'user': self.user,
                                                                                         'message': e}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))

        shutil.rmtree(self.backup_dir, True)
        self.last_state_datetime = datetime.datetime.now()
        self.save()

    def indent(self, level):
        self.xml.ignorableWhitespace('\n' + ' ' * 4 * level)

    def backup_objects(self):
        models = [Address, Contact, Contract, PhoneNumber, Project, Proposal, ProposalRow, Invoice, InvoiceRow, Expense]

        self.xml = SimplerXMLGenerator(self.stream, settings.DEFAULT_CHARSET)
        self.xml.startDocument()
        self.xml.startElement("aemanager", {"version" : version()['version']})

        for model in models:
            for object in model.objects.filter(owner=self.user):
                # do not export address of user profile
                if not(type(object) == Address and object.userprofile_set.count()):
                    self.indent(1)
                    self.xml.startElement(object._meta.object_name, {'uuid': object.uuid})
                    for field in object._meta.local_fields:
                        if field.name not in ['ownedobject_ptr']:
                            self.indent(2)
                            self.xml.startElement(field.name, {})
                            if getattr(object, field.name) is not None:
                                if type(field) == ForeignKey:
                                    related = getattr(object, field.name)
                                    if type(related) == Country:
                                        self.xml.addQuickElement("object", attrs={
                                          'country_code' : smart_unicode(related.country_code2)
                                        })
                                    else:
                                        self.xml.addQuickElement("object", attrs={
                                          'uuid' : smart_unicode(related.uuid)
                                        })
                                elif type(field) == OneToOneField:
                                    related = getattr(object, field.name)
                                    self.xml.addQuickElement("object", attrs={
                                      'uuid' : smart_unicode(related.uuid)
                                    })
                                else:
                                    self.xml.characters(field.value_to_string(object))
                            else:
                                self.xml.addQuickElement("None")
                            self.xml.endElement(field.name)

                    for field in object._meta.many_to_many:
                        self.indent(2)
                        self.xml.startElement(field.name, {})
                        for relobj in getattr(object, field.name).iterator():
                            self.indent(3)
                            self.xml.addQuickElement("object", attrs={
                              'uuid' : smart_unicode(relobj.uuid)
                            })
                        self.indent(2)
                        self.xml.endElement(field.name)

                    self.indent(1)
                    self.xml.endElement(smart_unicode(object._meta.object_name))

        self.indent(0)
        self.xml.endElement("aemanager")
        self.xml.endDocument()

    def backup_files(self):
        dirs = ['contract', 'logo', 'proposal']
        for dir in dirs:
            from_path = '%s%s/%s' % (settings.FILE_UPLOAD_DIR,
                                      self.user.get_profile().uuid,
                                      dir)
            to_path = '%s/%s' % (self.backup_dir, dir)
            if os.path.exists(from_path):
                shutil.copytree(from_path, to_path)

RESTORE_ACTION_ADD_MISSING = 1
RESTORE_ACTION_ADD_AND_UPDATE = 2
RESTORE_ACTION_DELETE_ALL_AND_RESTORE = 3
RESTORE_ACTION = ((RESTORE_ACTION_ADD_MISSING, _('Only add missing entries')),
                  (RESTORE_ACTION_ADD_AND_UPDATE, _('Add missing entries and update existing ones')),
                  (RESTORE_ACTION_DELETE_ALL_AND_RESTORE, _('Delete all your data and restore this backup')))

store = FileSystemStorage(location=settings.FILE_UPLOAD_DIR)

def restore_upload_to_handler(instance, filename):
    return "%s/restore/%s" % (instance.user.get_profile().uuid, unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore'))

class RestoreRequest(models.Model):
    user = models.OneToOneField(User)
    state = models.IntegerField(choices=BACKUP_RESTORE_STATE, default=BACKUP_RESTORE_STATE_PENDING)
    action = models.IntegerField(choices=RESTORE_ACTION, verbose_name=_('Action'), default=RESTORE_ACTION_ADD_MISSING)
    creation_datetime = models.DateTimeField()
    last_state_datetime = models.DateTimeField()
    error_message = models.CharField(max_length=255, null=True, blank=True)
    backup_file = models.FileField(upload_to=restore_upload_to_handler,
                                   null=True,
                                   blank=True,
                                   storage=store,
                                   verbose_name=_('Backup file'),
                                   help_text=_('max. %(FILE_MAX_SIZE)s') % {'FILE_MAX_SIZE': settings.FILE_MAX_SIZE})

    def __unicode__(self):
        return "%s %s %s" % (self.get_action_display(), self.get_state_display(), self.user)

    def clean_contract_contract_file(self, value):
        filename = os.path.basename(value)
        value = "%s/%s/%s" % (self.user.get_profile().uuid,
                              'contract',
                              filename)
        return value

    def clean_proposal_contract_file(self, value):
        filename = os.path.basename(value)
        value = "%s/%s/%s" % (self.user.get_profile().uuid,
                              'proposal',
                              filename)
        return value

    def restore(self):
        self.state = BACKUP_RESTORE_STATE_IN_PROGRESS
        self.save()

        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)
        try:
            self.tar = tarfile.open(self.backup_file.path, 'r:gz')

            # extract data.xml for parsing
            self.stream = self.tar.extractfile('backup/data.xml')
            self.restore_objects()

            self.restore_files()

            transaction.commit()
            transaction.leave_transaction_management()
            self.state = BACKUP_RESTORE_STATE_DONE
        except Exception as e:
            transaction.rollback()
            transaction.leave_transaction_management()
            self.state = BACKUP_RESTORE_STATE_ERROR
            self.error_message = e.__unicode__()
            mail_subject = _('Restore failed')
            mail_message = _('Restore for %(user)s failed with message : %(message)s') % {'user': self.user,
                                                                                         'message': e}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))

        self.save()

        # close and delete archive
        self.tar.close()
        os.remove(self.backup_file.path)
        self.backup_file = None

    def restore_objects(self):
        def get_clean_value(node, model_name, field):
            value = field.to_python(get_inner_text(node))
            clean_method_name = 'clean_%s_%s' % (model_name.lower(), node.nodeName)
            if hasattr(self, clean_method_name):
                clean_method = getattr(self, clean_method_name)
                value = clean_method(value)
            return value

        def get_inner_text(node):
            """
            Get all the inner text of a DOM node (recursively).
            """
            # inspired by http://mail.python.org/pipermail/xml-sig/2005-March/011022.html
            inner_text = []
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    inner_text.append(child.data)
                elif child.nodeType == child.ELEMENT_NODE:
                    inner_text.extend(getInnerText(child))
                else:
                    pass
            return u"".join(inner_text)

        def check_object_exists(node, klass):
            uuid = node.getAttribute('uuid')
            try:
                object = klass.objects.get(uuid=uuid)
                if object.owner <> self.user:
                    # import from another account, regenerate uuid to clone object
                    object = klass()
                    object.owner = self.user
                else:
                    if self.action == RESTORE_ACTION_ADD_MISSING:
                        self.substitution_map[uuid] = object.uuid
                        object = None
            except:
                # object not in database, can save it
                object = klass()
                object.uuid = uuid
                object.owner = self.user

            if object:
                self.substitution_map[uuid] = object.uuid

            return object

        def populate(object, node):
            field_name_list = ['%s' % (field.name) for field in object._meta.local_fields if field.name <> 'ownedobject_ptr']

            for child in node.childNodes:
                field_name = child.nodeName
                if field_name in field_name_list:
                    if child.getElementsByTagName('None'):
                        value = None
                    else:
                        field = object._meta.get_field(field_name)
                        value = get_clean_value(child, object._meta.object_name, field)
                        if type(field) == ForeignKey or type(field) == OneToOneField:
                            objects = child.getElementsByTagName('object')
                            if objects:
                                if field.related.parent_model == Country:
                                    country_code = objects[0].getAttribute('country_code')
                                    related_object = Country.objects.get(country_code2=country_code)
                                else:
                                    uuid = objects[0].getAttribute('uuid')
                                    try:
                                        real_uuid = self.substitution_map[uuid]
                                    except:
                                        raise Exception('Reference to a missing object')
                                    related_object = OwnedObject.objects.get(owner=self.user,
                                                                             uuid=real_uuid)
                                field_name = "%s_id" % (field_name)
                                value = related_object.pk

                    setattr(object, field_name, value)

        def populate_m2m(object, node):
            m2m_field_list = ['%s' % (field.name) for field in object._meta.many_to_many]
            m2m_data = []

            for child in node.childNodes:
                field_name = child.nodeName
                if field_name in m2m_field_list:
                    field = object._meta.get_field(field_name)
                    related_model = field.related.model
                    objects = child.getElementsByTagName('object')
                    uuids = []
                    for related_obj in objects:
                        uuids.append(related_obj.getAttribute('uuid'))
                    m2m_data.append({'object': object,
                                     'field_name': field_name,
                                     'related_model': related_model,
                                     'uuids': uuids})

            return m2m_data

        def do_restore():
            m2m_data = []
            for event, node in self.event_stream:
                if event == "START_ELEMENT" and node.nodeName in self.model_name_dict:
                    self.event_stream.expandNode(node)
                    object = check_object_exists(node, self.model_name_dict[node.nodeName])
                    if object:
                        populate(object, node)
                        object.save(user=self.user)
                        m2m_data = m2m_data + populate_m2m(object, node)

            for m2m in m2m_data:
                uuids = ['%s' % (self.substitution_map[uid]) for uid in m2m['uuids']]
                related_objects = m2m['related_model'].objects.filter(owner=self.user,
                                                                      uuid__in=uuids)

                setattr(m2m['object'], m2m['field_name'], related_objects)

        self.models = [Address, Contact, Contract, PhoneNumber, Project, Proposal, ProposalRow, Invoice, InvoiceRow, Expense]
        self.model_name_dict = {}
        for model in self.models:
            self.model_name_dict[model._meta.object_name] = model

        self.event_stream = pulldom.parse(self.stream)
        self.substitution_map = {}

        if self.action == RESTORE_ACTION_DELETE_ALL_AND_RESTORE:
            for model in self.models:
                for object in model.objects.filter(owner=self.user):
                    # do not export address of user profile
                    if not(type(object) == Address and object.userprofile_set.count()):
                        object.delete()
        do_restore()

    def restore_files(self):
        paths = ['proposal', 'contract']
        if self.action == RESTORE_ACTION_DELETE_ALL_AND_RESTORE:
            # delete proposal and contract directory
            for dir_path in paths:
                target_dir = '%s%s/%s' % (settings.FILE_UPLOAD_DIR,
                                          self.user.get_profile().uuid,
                                          dir_path)
                shutil.rmtree(target_dir, True)

        for member in self.tar:
            dir_path = os.path.dirname(member.name).replace('backup/', '')
            if dir_path in paths:
                filename = os.path.basename(member.name)
                target_dir = '%s%s/%s' % (settings.FILE_UPLOAD_DIR,
                                          self.user.get_profile().uuid,
                                          dir_path)
                mkdir_p(target_dir)
                target_filename = '%s/%s' % (target_dir,
                                              filename)

                if not(self.action == RESTORE_ACTION_ADD_MISSING and os.path.exists(target_filename)):
                    target_file = open(target_filename, 'w')
                    file = self.tar.extractfile(member)
                    target_file.write(file.read())
                    target_file.close()
