from django import forms
from backup.models import BackupRequest, RestoreRequest
from django.utils.translation import ugettext_lazy as _

class BackupForm(forms.ModelForm):
    backup_or_restore = forms.CharField(initial='backup', widget=forms.HiddenInput())

    class Meta:
        model = BackupRequest
        exclude = ['user', 'state', 'creation_datetime', 'last_state_datetime', 'error_message']

class RestoreForm(forms.ModelForm):
    backup_or_restore = forms.CharField(initial='restore', widget=forms.HiddenInput())

    class Meta:
        model = RestoreRequest
        exclude = ['user', 'state', 'creation_datetime', 'last_state_datetime', 'error_message']

class CSVForm(forms.Form):
    begin_date = forms.DateField(label=_('From date'), required=False, help_text=_('Optional. If not set, export from the first invoice'))
    end_date = forms.DateField(label=_('To date'), required=False, help_text=_('Optional. If not set, export until now'))

    def __init__(self, *args, **kwargs):
        super(CSVForm, self).__init__(*args, **kwargs)
        self.fields['begin_date'].widget.attrs['class'] = 'date'
        self.fields['end_date'].widget.attrs['class'] = 'date'
