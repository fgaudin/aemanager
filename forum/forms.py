from django import forms
from forum.models import Topic, Message

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
