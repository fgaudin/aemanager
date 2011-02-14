from django import forms
from bugtracker.models import Issue, Comment

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        exclude = ['owner', 'update_date', 'state']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ['owner', 'update_date', 'issue']
