from django.forms import ModelForm
from notification.models import Notification

class NotificationForm(ModelForm):
    class Meta:
        model = Notification
        exclude = ['user']
