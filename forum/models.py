from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from core.templatetags.modeltags import display_name
from django.db.models.signals import post_save

class Topic(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    views = models.IntegerField(default=0, verbose_name=_('Views'))

    def __unicode__(self):
        return u'%s' % (self.title)

    def first_message(self):
        return self.messages.all().order_by('creation_date')[0]

    def last_message(self):
        try:
            return self.messages.all().order_by('-creation_date')[0]
        except:
            return None

class Message(models.Model):
    body = models.TextField(verbose_name=_('Body'))
    author = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Author'), related_name="forum_messages")
    creation_date = models.DateTimeField(verbose_name=_('Created at'))
    topic = models.ForeignKey(Topic, related_name='messages')

    class Meta:
        ordering = ['creation_date']

    def __unicode__(self):
        return "message %d by %s" % (self.pk, self.author)

    def display_author(self):
        return display_name(self.author)

    def author_message_count(self):
        return Message.objects.filter(author=self.author).count()

class MessageNotification(models.Model):
    message = models.ForeignKey(Message, verbose_name=_('Message'))

    class Meta:
        ordering = ['message__creation_date']

    def __unicode__(self):
        return "notification for message %s" % (self.message)
