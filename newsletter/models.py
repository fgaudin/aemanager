from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

USER_TYPE_SUBSCRIPTION_PAID = 1
USER_TYPE_SUBSCRIPTION_TRIAL = 2
USER_TYPE_SUBSCRIPTION_EXPIRED = 3
USER_TYPE = ((USER_TYPE_SUBSCRIPTION_PAID, _('Users who have paid subscription')),
             (USER_TYPE_SUBSCRIPTION_TRIAL, _('Users still in trial')),
             (USER_TYPE_SUBSCRIPTION_EXPIRED, _('Users with subscription expired')))

class Message(models.Model):
    to = models.IntegerField(verbose_name=_('User type'), choices=USER_TYPE)
    subject = models.CharField(verbose_name=_('Subject'), max_length=100)
    message = models.TextField(verbose_name=_('Message'), help_text=_('Signature will be automatically added'))
    update_datetime = models.DateTimeField(verbose_name=_('Update date'))
    sent = models.BooleanField(verbose_name=_('Sent'), default=False)

    class Meta:
        ordering = ['-update_datetime']
