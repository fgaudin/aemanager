from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_words

class Announcement(models.Model):
    content = models.TextField(verbose_name=_('Announcement'))
    enabled = models.BooleanField(default=False, verbose_name=_('Enabled'))

    def __unicode__(self):
        return truncate_words(self.content, 10)
