from django.forms import ModelForm
from contact.models import Address, Contact, PhoneNumber, CONTACT_TYPE, \
    CONTACT_TYPE_PERSON
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import Textarea

class AddressForm(ModelForm):
    street = forms.CharField(label=_('Street'), widget=Textarea)
    zipcode = forms.CharField(max_length=10, label=_('Zip code'))
    city = forms.CharField(max_length=255, label=_('City'))

    class Meta:
        model = Address
        exclude = ['owner', 'uuid']

class ContactForm(ModelForm):
    contact_type = forms.ChoiceField(label=_('Type'),
                                     choices=CONTACT_TYPE,
                                     required=True,
                                     widget=forms.RadioSelect(),
                                     initial=CONTACT_TYPE_PERSON)
    company_id = forms.CharField(max_length=50, required=True, label=_('Company id')) # SIRET for France

    class Meta:
        model = Contact
        exclude = ['owner', 'uuid', 'address']

class PhoneNumberForm(ModelForm):
    class Meta:
        model = PhoneNumber
        exclude = ['owner', 'uuid']

    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        self.fields['default'].widget.attrs['class'] = 'default-phonenumber'

class ContactSearchForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=False)
    email = forms.CharField(label=_('Email'), required=False)
    phonenumber = forms.CharField(label=_('Phone number'), required=False)
