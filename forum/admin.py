from django.contrib import admin
from forum.models import Topic, Message, MessageNotification

admin.site.register(Topic)
admin.site.register(Message)
admin.site.register(MessageNotification)
