# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from core.models import OwnedObject

class Country(models.Model):
    country_code2 = models.CharField(max_length=2)
    country_code3 = models.CharField(max_length=3)
    country_name = models.CharField(max_length=50)

    class Meta:
        ordering = ['country_name']

    def __unicode__(self):
        return self.country_name

class Address(OwnedObject):
    street = models.TextField(blank=True, default='', verbose_name=_('Street'))
    zipcode = models.CharField(max_length=10, blank=True, default='', verbose_name=_('Zip code'))
    city = models.CharField(max_length=255, blank=True, default='', verbose_name=_('City'))
    country = models.ForeignKey(Country, blank=True, null=True, verbose_name=_('Country'))

    def __unicode__(self):
        return "%s, %s %s, %s" % (self.street, self.zipcode, self.city, self.country)

CONTACT_TYPE_PERSON = 1
CONTACT_TYPE_COMPANY = 2
CONTACT_TYPE = ((CONTACT_TYPE_PERSON, _('Person')),
                (CONTACT_TYPE_COMPANY, _('Company')))

class Contact(OwnedObject):
    contact_type = models.IntegerField(choices=CONTACT_TYPE, verbose_name=_('Type'))
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    firstname = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Firstname'))
    function = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Function'))
    company_id = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Company id')) # SIRET for France
    legal_form = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Legal form'))
    representative = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Representative'))
    representative_function = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Representative function'))
    email = models.EmailField(blank=True, default='', verbose_name=_('Email'))
    contacts = models.ManyToManyField("self", blank=True, null=True, verbose_name=_('Related contacts'))
    address = models.ForeignKey(Address, verbose_name=_('Address'))
    comment = models.TextField(blank=True, default='', verbose_name=_('Comment'))

    def __unicode__(self):
        name = self.name
        if self.firstname:
            name = "%s %s" % (name, self.firstname)
        return name

    def is_company(self):
        return self.contact_type == CONTACT_TYPE_COMPANY

    def default_phonenumber(self):
        default_phonenumber = self.phonenumber_set.filter(default=True)
        if len(default_phonenumber):
            return default_phonenumber[0]
        else:
            default_phonenumber = self.phonenumber_set.all()
            if len(default_phonenumber):
                return default_phonenumber[0]
        return None

PHONENUMBER_TYPE_HOME = 1
PHONENUMBER_TYPE_WORK = 2
PHONENUMBER_TYPE_MOBILE = 3
PHONENUMBER_TYPE_FAX = 4
PHONENUMBER_TYPE = ((PHONENUMBER_TYPE_HOME, _('Home')),
                    (PHONENUMBER_TYPE_WORK, _('Work')),
                    (PHONENUMBER_TYPE_MOBILE, _('Mobile')),
                    (PHONENUMBER_TYPE_FAX, _('Fax')))

class PhoneNumber(OwnedObject):
    type = models.IntegerField(choices=PHONENUMBER_TYPE)
    number = models.CharField(max_length=20)
    default = models.BooleanField(verbose_name=_('Default'))
    contact = models.ForeignKey(Contact)

    class Meta:
        ordering = ['-default', 'type']

    def __unicode__(self):
        return ('%s : %s' % (self.get_type_display(), self.number))
