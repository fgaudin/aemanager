from django.forms import ModelForm
from contact.models import Address, Contact, PhoneNumber, CONTACT_TYPE, \
    CONTACT_TYPE_PERSON
from django import forms
from django.utils.translation import ugettext_lazy as _

class AddressForm(ModelForm):
    class Meta:
        model = Address
        exclude = ['owner']

class ContactForm(ModelForm):
    contact_type = forms.ChoiceField(label=_('Type'),
                                     choices=CONTACT_TYPE,
                                     required=True,
                                     widget=forms.RadioSelect(),
                                     initial=CONTACT_TYPE_PERSON)

    class Meta:
        model = Contact
        exclude = ['owner', 'address']

class PhoneNumberForm(ModelForm):
    class Meta:
        model = PhoneNumber
        exclude = ['owner']

class ContactSearchForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=False)
    email = forms.CharField(label=_('Email'), required=False)
    phonenumber = forms.CharField(label=_('Phone number'), required=False)
