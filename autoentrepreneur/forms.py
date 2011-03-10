from django.forms import ModelForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from autoentrepreneur.models import UserProfile, AUTOENTREPRENEUR_ACTIVITY, \
    AUTOENTREPRENEUR_PAYMENT_OPTION, AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY

class UserProfileForm(ModelForm):
    company_name = forms.CharField(required=False, max_length=255, label=_('Company name'))
    company_id = forms.CharField(max_length=50, label=_('Company id')) # SIRET for France
    activity = forms.ChoiceField(choices=AUTOENTREPRENEUR_ACTIVITY, label=_('Activity'))
    professional_category = forms.ChoiceField(choices=AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY, label=_('Professional category'))
    creation_date = forms.DateField(label=_('Creation date'), help_text=_('format: mm/dd/yyyy'))
    creation_help = forms.BooleanField(required=False, label=_('Creation help')) # accre
    freeing_tax_payment = forms.BooleanField(required=False, label=_('Freeing tax payment')) # versement liberatoire
    payment_option = forms.ChoiceField(choices=AUTOENTREPRENEUR_PAYMENT_OPTION, label=_('Payment option'))

    class Meta:
        model = UserProfile
        exclude = ['user', 'address', 'unregister_datetime']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['creation_date'].widget.attrs['class'] = 'date'
