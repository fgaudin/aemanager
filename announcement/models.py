from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_words

class Announcement(models.Model):
    content = models.TextField(verbose_name=_('Announcement'))
    enabled = models.BooleanField(default=False, verbose_name=_('Enabled'), db_index=True)
    ordering = models.IntegerField(default=1, verbose_name=_('Order'), db_index=True)
    important = models.BooleanField(default=False, verbose_name=_('Important'), db_index=True)

    class Meta:
        ordering = ['ordering']

    def __unicode__(self):
        return truncate_words(self.content, 10)
