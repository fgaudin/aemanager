from django import forms
from newsletter.models import Message

class EmailUsersForm(forms.ModelForm):
    class Meta:
        model = Message
        exclude = ['update_datetime']

    def __init__(self, *args, **kwargs):
        super(EmailUsersForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['class'] = 'mail-subject'
