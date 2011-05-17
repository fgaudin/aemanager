from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class Notification(models.Model):
    user = models.OneToOneField(User)
    notify_late_invoices = models.BooleanField(default=True, verbose_name=_('Notify late invoices'), help_text=_('You will receive an email when a payment date has expired'))
    notify_invoices_to_send = models.BooleanField(default=True, verbose_name=_('Notify invoices to send'), help_text=_('You will receive an email when an edition date of an edited invoice has expired'))
    notify_bug_comments = models.BooleanField(default=True, verbose_name=_('Notify bug comments'), help_text=_('You will receive an email when a bug you posted or commented has a new comment'))
