from django.forms import ModelForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import PasswordInput
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationFormUniqueEmail
from django.contrib.sites.models import Site

class UserForm(ModelForm):
    first_name = forms.CharField(label=_('first name'), max_length=30)
    last_name = forms.CharField(label=_('last name'), max_length=30)

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class PasswordForm(forms.Form):
    current_password = forms.CharField(label=_('Current password'), widget=PasswordInput(render_value=False))
    new_password = forms.CharField(label=_('New password'), widget=PasswordInput(render_value=False))
    retyped_new_password = forms.CharField(label=_('Retype password'), widget=PasswordInput(render_value=False))

    def clean(self):
        cleaned_data = self.cleaned_data
        new_password = cleaned_data.get("new_password")
        retyped_new_password = cleaned_data.get("retyped_new_password")

        if new_password <> retyped_new_password:
            self._errors["retyped_new_password"] = self.error_class([_("Password doesn't match")])
            del cleaned_data['retyped_new_password']

        return cleaned_data

class RegistrationFormUniqueEmailAndTos(RegistrationFormUniqueEmail):
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'required'}),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})

    def __init__(self, *args, **kwargs):
        super(RegistrationFormUniqueEmailAndTos, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = _('only letters, numbers and underscores are accepted')
        # only to override a missing translation in django-registration
        self.fields['username'].error_messages['invalid'] = _("This value must contain only letters, numbers and underscores.")
        self.fields['email'].help_text = _('must be valid to activate your account')

    def clean_username(self):
        """
        Validate that the username is different from "demo"
        to protect demo account
        """
        super(RegistrationFormUniqueEmailAndTos, self).clean_username()
        if self.cleaned_data['username'] == 'demo':
            raise forms.ValidationError(_("A user with that username already exists."))
        return self.cleaned_data['username']

class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(label=_('Email'), widget=forms.TextInput(attrs={'class': 'required',
                                                                             'maxlength':75}))

class ContactUsForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=50)
    email = forms.EmailField(label=_('Email'))
    subject = forms.CharField(label=_('Subject'))
    message = forms.CharField(label=_('Message'), widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(ContactUsForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['class'] = 'mail-subject'
