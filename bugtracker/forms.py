from django import forms
from bugtracker.models import Issue, Comment

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        exclude = ['owner', 'uuid', 'update_date', 'state']

    def __init__(self, *args, **kwargs):
        super(IssueForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['class'] = 'mail-subject'

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ['owner', 'uuid', 'update_date', 'issue']
