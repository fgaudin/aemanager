from django.forms import ModelForm
from django.contrib.auth.models import User
from django import forms
from django.forms.widgets import PasswordInput
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationFormUniqueEmail

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
                             label=_(u'I have read and agree to the Terms of Sale and Service'),
                             error_messages={'required': _("You must agree to the terms to register")})

class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(label=_('Email'), widget=forms.TextInput(attrs={'class': 'required',
                                                                             'maxlength':75}))
