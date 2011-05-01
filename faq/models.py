from django.db import models
from django.utils.translation import ugettext_lazy as _

class Category(models.Model):
    label = models.CharField(max_length=255, verbose_name=_('Label'))
    order = models.IntegerField(default=0, verbose_name=_('Order'))

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return self.label

class QuestionAnswer(models.Model):
    question = models.TextField(verbose_name=_('Question'))
    answer = models.TextField(verbose_name=_('Answer'))
    category = models.ForeignKey(Category, verbose_name=_('Category'), related_name='questions')
    order = models.IntegerField(default=0, verbose_name=_('Order'))

    class Meta:
        ordering = ['category', 'order']

    def __unicode__(self):
        return self.question
