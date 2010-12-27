from django.db import models
from core.models import OwnedObject
from django.utils.translation import ugettext_lazy as _, ugettext
from contact.models import Contact
from django.core.urlresolvers import reverse
from project.models import Row, Proposal, update_row_amount
from django.db.models.aggregates import Sum
from django.db.models.signals import post_save, pre_save

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

class InvoiceAmountError(Exception):
    pass

class InvoiceIdNotUniqueError(Exception):
    pass

INVOICE_STATE_EDITED = 1
INVOICE_STATE_SENT = 2
INVOICE_STATE_PAID = 3
INVOICE_STATE = ((INVOICE_STATE_EDITED, _('Edited')),
              (INVOICE_STATE_SENT, _('Sent')),
              (INVOICE_STATE_PAID, _('Paid')))

class Invoice(OwnedObject):
    customer = models.ForeignKey(Contact, blank=True, null=True, verbose_name=_('Customer'))
    invoice_id = models.IntegerField(verbose_name=_("Invoice id"))
    state = models.IntegerField(choices=INVOICE_STATE, default=INVOICE_STATE_EDITED, verbose_name=_("State"))
    amount = models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=2, verbose_name=_("Amount"))
    edition_date = models.DateField(verbose_name=_("Edition date"))
    payment_date = models.DateField(blank=True, null=True, verbose_name=_("Payment date"))
    paid_date = models.DateField(blank=True, null=True, verbose_name=_("Paid date"))
    execution_begin_date = models.DateField(blank=True, null=True, verbose_name=_("Execution begin date"))
    execution_end_date = models.DateField(blank=True, null=True, verbose_name=_("Execution end date"))
    penalty_date = models.DateField(blank=True, null=True, verbose_name=_("Penalty date"))
    penalty_rate = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2, verbose_name=_("Penalty rate"))
    discount_conditions = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Discount conditions"))

    def __unicode__(self):
        return "<a href=\"%s\">%s</a>" % (reverse('invoice_detail', kwargs={'id' : self.id}), ugettext("invoice #%d") % (self.invoice_id))

    def isInvoiceIdUnique(self, owner):
        invoices = Invoice.objects.filter(owner=owner,
                                          invoice_id=self.invoice_id)
        if self.id:
            invoices = invoices.exclude(id=self.id)

        if len(invoices):
            return False

        return True

    def save(self, force_insert=False, force_update=False, using=None, user=None):
        if not self.isInvoiceIdUnique(user):
            raise InvoiceIdNotUniqueError(ugettext("Invoice id must be unique"))
        super(Invoice, self).save(force_insert, force_update, using, user)

    def toPdf(self):
        """
        Generate a PDF file for the invoice
        """
        pass

class InvoiceRowAmountError(Exception):
    pass

class InvoiceRow(Row):
    invoice = models.ForeignKey(Invoice, related_name="invoice_rows")
    proposal = models.ForeignKey(Proposal, related_name="invoice_rows")
    balance_payments = models.BooleanField(verbose_name=_('Balance payments for the proposal'))

    def isAmountValid(self):
        invoicerows = InvoiceRow.objects.filter(proposal=self.proposal)
        if self.id:
            invoicerows = invoicerows.exclude(id=self.id)
        invoicerow_sum = float(invoicerows.aggregate(sum=Sum('amount'))['sum'] or 0)
        invoicerow_amount = float(self.unit_price) * float(self.quantity)
        if float(self.proposal.amount) < (invoicerow_sum + invoicerow_amount):
            return False

        return True

    def save(self, force_insert=False, force_update=False, using=None, user=None):
        if not self.isAmountValid():
            raise InvoiceRowAmountError(ugettext("Sum of invoice row amount can't exceed proposal amount"))
        super(InvoiceRow, self).save(force_insert, force_update, using, user)

def update_invoice_amount(sender, instance, created, **kwargs):
    row = instance
    invoice = row.invoice
    invoice.amount = invoice.invoice_rows.all().aggregate(sum=Sum('amount'))['sum'] or 0
    invoice.save(user=invoice.owner)

pre_save.connect(update_row_amount, sender=InvoiceRow)
post_save.connect(update_invoice_amount, sender=InvoiceRow)
