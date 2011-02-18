from django.db import models
from core.models import OwnedObject
from django.utils.translation import ugettext_lazy as _, ugettext
from contact.models import Contact
from django.core.urlresolvers import reverse
from project.models import Row, Proposal, update_row_amount, \
    ROW_CATEGORY_SERVICE, ROW_CATEGORY, PROPOSAL_STATE_ACCEPTED, ProposalRow
from django.db.models.aggregates import Sum, Min
from django.db.models.signals import post_save, pre_save, post_delete
import datetime

PAYMENT_TYPE_CASH = 1
PAYMENT_TYPE_BANK_CARD = 2
PAYMENT_TYPE_TRANSFER = 3
PAYMENT_TYPE_CHECK = 4
PAYMENT_TYPE = ((PAYMENT_TYPE_CASH, _('Cash')),
                (PAYMENT_TYPE_BANK_CARD, _('Bank card')),
                (PAYMENT_TYPE_TRANSFER, _('Transfer')),
                (PAYMENT_TYPE_CHECK, _('Check')))

class Expense(OwnedObject):
    date = models.DateField(verbose_name=_('Date'), help_text=_('format: mm/dd/yyyy'))
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

class InvoiceManager(models.Manager):
    def get_paid_sales(self, owner, year=None):
        if not year:
            year = datetime.date.today().year
        amount_sum = self.filter(state=INVOICE_STATE_PAID,
                                 owner=owner,
                                 paid_date__year=year).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_paid_service_sales(self, owner, year=None):
        if not year:
            year = datetime.date.today().year
        amount_sum = InvoiceRow.objects.filter(invoice__state=INVOICE_STATE_PAID,
                                               owner=owner,
                                               category=ROW_CATEGORY_SERVICE,
                                               invoice__paid_date__year=year).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_waiting_payments(self, owner):
        amount_sum = self.filter(state=INVOICE_STATE_SENT,
                                 owner=owner).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_waiting_service_payments(self, owner):
        amount_sum = InvoiceRow.objects.filter(invoice__state=INVOICE_STATE_SENT,
                                               owner=owner,
                                               category=ROW_CATEGORY_SERVICE).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_late_invoices(self, owner):
        late_invoices = self.filter(state=INVOICE_STATE_SENT,
                                    payment_date__lt=datetime.date.today(),
                                    owner=owner)
        return late_invoices

    def get_invoices_to_send(self, owner):
        invoices_to_send = self.filter(state=INVOICE_STATE_EDITED,
                                       edition_date__lte=datetime.date.today(),
                                       owner=owner)
        return invoices_to_send

    def get_paid_sales_for_period(self, owner, begin_date, end_date):
        if not begin_date or not end_date:
            return 0
        amount_sum = self.filter(state=INVOICE_STATE_PAID,
                                 owner=owner,
                                 paid_date__gte=begin_date,
                                 paid_date__lte=end_date).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_first_invoice_paid_date(self, owner):
        return self.filter(owner=owner).aggregate(min_date=Min('paid_date'))['min_date']

    def get_paid_invoices(self, owner, begin_date=None):
        if not begin_date:
            return self.filter(state=INVOICE_STATE_PAID,
                               owner=owner,
                               paid_date__year=datetime.date.today().year).order_by('paid_date')
        else:
            return self.filter(state=INVOICE_STATE_PAID,
                               owner=owner,
                               paid_date__lte=datetime.date.today(),
                               paid_date__gte=begin_date).order_by('paid_date')

    def get_waiting_invoices(self, owner):
        return self.filter(state__lte=INVOICE_STATE_SENT,
                           owner=owner).order_by('payment_date')

    def get_to_be_invoiced(self, owner):
        accepted_proposal_amount_sum = Proposal.objects.filter(state=PROPOSAL_STATE_ACCEPTED,
                                                   owner=owner).extra(where=['project_proposal.ownedobject_ptr_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                                                 params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).aggregate(amount=Sum('amount'))
        invoicerows_to_exclude = InvoiceRow.objects.extra(where=['accounts_invoicerow.proposal_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                          params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).exclude(invoice__state=INVOICE_STATE_EDITED).filter(owner=owner).aggregate(amount=Sum('amount'))
        return (accepted_proposal_amount_sum['amount'] or 0) - (invoicerows_to_exclude['amount'] or 0)

    def get_service_to_be_invoiced(self, owner):
        accepted_proposal_amount_sum = ProposalRow.objects.filter(proposal__state=PROPOSAL_STATE_ACCEPTED,
                                                                  category=ROW_CATEGORY_SERVICE,
                                                                  owner=owner).extra(where=['project_proposal.ownedobject_ptr_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                                                 params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).aggregate(amount=Sum('amount'))
        invoicerows_to_exclude = InvoiceRow.objects.filter(proposal__state=PROPOSAL_STATE_ACCEPTED,
                                                           category=ROW_CATEGORY_SERVICE,
                                                           owner=owner).extra(where=['accounts_invoicerow.proposal_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                                             params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).exclude(invoice__state=INVOICE_STATE_EDITED).filter(owner=owner).aggregate(amount=Sum('amount'))
        return (accepted_proposal_amount_sum['amount'] or 0) - (invoicerows_to_exclude['amount'] or 0)

class Invoice(OwnedObject):
    customer = models.ForeignKey(Contact, blank=True, null=True, verbose_name=_('Customer'))
    invoice_id = models.IntegerField(verbose_name=_("Invoice id"))
    state = models.IntegerField(choices=INVOICE_STATE, default=INVOICE_STATE_EDITED, verbose_name=_("State"))
    amount = models.DecimalField(blank=True, max_digits=12, decimal_places=2, default=0, verbose_name=_("Amount"))
    edition_date = models.DateField(verbose_name=_("Edition date"), help_text=_('format: mm/dd/yyyy'))
    payment_date = models.DateField(verbose_name=_("Payment date"), help_text=_('format: mm/dd/yyyy'))
    payment_type = models.IntegerField(choices=PAYMENT_TYPE, verbose_name=_('Payment type'))
    paid_date = models.DateField(blank=True, null=True, verbose_name=_("Paid date"), help_text=_('format: mm/dd/yyyy'))
    execution_begin_date = models.DateField(blank=True, null=True, verbose_name=_("Execution begin date"), help_text=_('format: mm/dd/yyyy'))
    execution_end_date = models.DateField(blank=True, null=True, verbose_name=_("Execution end date"), help_text=_('format: mm/dd/yyyy'))
    penalty_date = models.DateField(blank=True, null=True, verbose_name=_("Penalty date"), help_text=_('format: mm/dd/yyyy'))
    penalty_rate = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2, verbose_name=_("Penalty rate"))
    discount_conditions = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Discount conditions"))

    objects = InvoiceManager()

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

    def getNature(self):
        natures = self.invoice_rows.values('category').distinct()
        result = []
        natures_dict = dict(ROW_CATEGORY)
        for nature in natures:
            result.append(unicode(natures_dict[nature['category']]))

        return " & ".join(result)


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
    balance_payments = models.BooleanField(verbose_name=_('Balance payments for the proposal'), help_text=_('"Balancing payments for the proposal" means there will be no future invoices for the selected proposal. Thus the amount remaining to invoice for this proposal will fall to zero and its state will be set to "balanced" when all invoices are paid.'))

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

def update_invoice_amount(sender, instance, created=None, **kwargs):
    row = instance
    invoice = row.invoice
    invoice.amount = invoice.invoice_rows.all().aggregate(sum=Sum('amount'))['sum'] or 0
    invoice.save(user=invoice.owner)

pre_save.connect(update_row_amount, sender=InvoiceRow)
post_save.connect(update_invoice_amount, sender=InvoiceRow)
post_delete.connect(update_invoice_amount, sender=InvoiceRow)
