from django.db import models
from core.models import OwnedObject
from django.utils.translation import ugettext_lazy as _

PAYMENT_TYPE_CASH = 1
PAYMENT_TYPE_BANK_CARD = 2
PAYMENT_TYPE_TRANSFER = 3
PAYMENT_TYPE_CHECK = 4
PAYMENT_TYPE = ((PAYMENT_TYPE_CASH, _('Cash')),
                (PAYMENT_TYPE_BANK_CARD, _('Bank card')),
                (PAYMENT_TYPE_TRANSFER, _('Transfer')),
                (PAYMENT_TYPE_CHECK, _('Check')))

class Expense(OwnedObject):
    date = models.DateField(verbose_name=_('Date'))
    reference = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Reference'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Amount'))
    payment_type = models.IntegerField(choices=PAYMENT_TYPE, verbose_name=_('Payment type'))
    description = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Description'))
