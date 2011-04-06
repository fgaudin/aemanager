from django import forms
from backup.models import BackupRequest, RestoreRequest

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
