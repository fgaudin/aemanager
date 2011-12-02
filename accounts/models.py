# coding=utf-8
from decimal import Decimal
from django.utils.formats import localize
import datetime
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from django.db import models, connection
from core.models import OwnedObject
from django.utils.translation import ugettext_lazy as _, ugettext
from contact.models import Contact
from django.core.urlresolvers import reverse
from project.models import Row, Proposal, update_row_amount, \
    ROW_CATEGORY_SERVICE, ROW_CATEGORY, PROPOSAL_STATE_ACCEPTED, ProposalRow, \
    VAT_RATES_2_1, VAT_RATES_5_5, VAT_RATES_19_6
from django.db.models.aggregates import Sum, Min, Max
from django.db.models.signals import post_save, pre_save, post_delete
from django.core.validators import MaxValueValidator
from accounts.utils.pdf import InvoiceTemplate

PAYMENT_TYPE_CASH = 1
PAYMENT_TYPE_BANK_CARD = 2
PAYMENT_TYPE_TRANSFER = 3
PAYMENT_TYPE_CHECK = 4
PAYMENT_TYPE_PAYPAL = 5
PAYMENT_TYPE_DEBIT = 6
PAYMENT_TYPE = ((PAYMENT_TYPE_CASH, _('Cash')),
                (PAYMENT_TYPE_BANK_CARD, _('Bank card')),
                (PAYMENT_TYPE_TRANSFER, _('Transfer')),
                (PAYMENT_TYPE_CHECK, _('Check')),
                (PAYMENT_TYPE_PAYPAL, _('Paypal')),
                (PAYMENT_TYPE_DEBIT, _('Debit')))

class Expense(OwnedObject):
    date = models.DateField(verbose_name=_('Date'), help_text=_('format: mm/dd/yyyy'), db_index=True)
    reference = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Reference'))
    supplier = models.CharField(max_length=70, blank=True, null=True, verbose_name=_('Supplier'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Amount'))
    payment_type = models.IntegerField(choices=PAYMENT_TYPE, verbose_name=_('Payment type'))
    description = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Description'))

class InvoiceAmountError(Exception):
    pass

class InvoiceIdNotUniqueError(Exception):
    pass

class InvalidInvoiceIdError(Exception):
    pass

MAX_INVOICE_ID = 999999999

INVOICE_STATE_EDITED = 1
INVOICE_STATE_SENT = 2
INVOICE_STATE_PAID = 3
INVOICE_STATE = ((INVOICE_STATE_EDITED, _('Edited')),
              (INVOICE_STATE_SENT, _('Sent')),
              (INVOICE_STATE_PAID, _('Paid')))

class InvoiceManager(models.Manager):
    def get_next_invoice_id(self, owner):
        return (Invoice.objects.filter(owner=owner).aggregate(invoice_id=Max('invoice_id'))['invoice_id'] or 0) + 1

    def get_paid_sales(self, owner, reference_date=None):
        if not reference_date:
            reference_date = datetime.date.today()
        amount_sum = self.filter(state=INVOICE_STATE_PAID,
                                 owner=owner,
                                 paid_date__lte=reference_date,
                                 paid_date__year=reference_date.year).aggregate(sales=Sum('amount'))
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

    def get_late_invoices_for_notification(self):
        late_invoices = self.filter(state=INVOICE_STATE_SENT,
                                    payment_date__lt=datetime.date.today(),
                                    owner__notification__notify_late_invoices=True)
        return late_invoices

    def get_invoices_to_send(self, owner):
        invoices_to_send = self.filter(state=INVOICE_STATE_EDITED,
                                       edition_date__lte=datetime.date.today(),
                                       owner=owner)
        return invoices_to_send

    def get_invoices_to_send_for_notification(self):
        invoices_to_send = self.filter(state=INVOICE_STATE_EDITED,
                                       edition_date__lte=datetime.date.today(),
                                       owner__notification__notify_invoices_to_send=True)
        return invoices_to_send

    def get_paid_sales_for_period(self, owner, begin_date, end_date):
        if not begin_date or not end_date:
            return 0
        amount_sum = self.filter(state=INVOICE_STATE_PAID,
                                 owner=owner,
                                 paid_date__gte=begin_date,
                                 paid_date__lte=end_date).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_waiting_sales_for_period(self, owner, end_date, begin_date=None):
        if not end_date:
            return 0
        amount_sum = self.filter(state__lte=INVOICE_STATE_SENT,
                                 owner=owner,
                                 payment_date__lte=end_date)
        if begin_date:
            amount_sum = amount_sum.filter(payment_date__gte=begin_date)
        amount_sum = amount_sum.aggregate(waiting=Sum('amount'))
        return amount_sum['waiting'] or 0

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
        # exclude amount found in sent or paid invoices referencing accepted proposal, aka computing already invoiced from not sold proposal
        invoicerows_to_exclude = InvoiceRow.objects.extra(where=['accounts_invoicerow.proposal_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                          params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).exclude(invoice__state=INVOICE_STATE_EDITED).filter(owner=owner).aggregate(amount=Sum('amount'))

        # adding invoice rows of edited invoices which don't have proposal linked
        invoicerows_whithout_proposals = InvoiceRow.objects.filter(owner=owner,
                                                                   proposal=None,
                                                                   invoice__state=INVOICE_STATE_EDITED).aggregate(amount=Sum('amount'))
        return (accepted_proposal_amount_sum['amount'] or 0) - (invoicerows_to_exclude['amount'] or 0) + (invoicerows_whithout_proposals['amount'] or 0)

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

    def get_vat_for_period(self, owner, begin_date, end_date):
        if not begin_date or not end_date:
            return 0
        amount_sum_2_1 = InvoiceRow.objects.filter(vat_rate=VAT_RATES_2_1,
                                                   invoice__state=INVOICE_STATE_PAID,
                                                   invoice__owner=owner,
                                                   invoice__paid_date__gte=begin_date,
                                                   invoice__paid_date__lte=end_date).aggregate(vat=Sum('amount'))
        amount_sum_5_5 = InvoiceRow.objects.filter(vat_rate=VAT_RATES_5_5,
                                                   invoice__state=INVOICE_STATE_PAID,
                                                   invoice__owner=owner,
                                                   invoice__paid_date__gte=begin_date,
                                                   invoice__paid_date__lte=end_date).aggregate(vat=Sum('amount'))
        amount_sum_19_6 = InvoiceRow.objects.filter(vat_rate=VAT_RATES_19_6,
                                                    invoice__state=INVOICE_STATE_PAID,
                                                    invoice__owner=owner,
                                                    invoice__paid_date__gte=begin_date,
                                                    invoice__paid_date__lte=end_date).aggregate(vat=Sum('amount'))
        return (amount_sum_2_1['vat'] or 0) * VAT_RATES_2_1 / 100\
               + (amount_sum_5_5['vat'] or 0) * VAT_RATES_5_5 / 100\
               + (amount_sum_19_6['vat'] or 0) * VAT_RATES_19_6 / 100

class Invoice(OwnedObject):
    customer = models.ForeignKey(Contact, blank=True, null=True, verbose_name=_('Customer'))
    invoice_id = models.IntegerField(verbose_name=_("Invoice id"))
    state = models.IntegerField(choices=INVOICE_STATE, default=INVOICE_STATE_EDITED, verbose_name=_("State"), db_index=True)
    amount = models.DecimalField(blank=True, max_digits=12, decimal_places=2, default=0, verbose_name=_("Amount"))
    edition_date = models.DateField(verbose_name=_("Edition date"), help_text=_('format: mm/dd/yyyy'), db_index=True)
    payment_date = models.DateField(verbose_name=_("Payment date"), help_text=_('format: mm/dd/yyyy'), db_index=True)
    payment_type = models.IntegerField(choices=PAYMENT_TYPE, blank=True, null=True, verbose_name=_('Payment type'))
    paid_date = models.DateField(blank=True, null=True, verbose_name=_("Paid date"), help_text=_('format: mm/dd/yyyy'), db_index=True)
    execution_begin_date = models.DateField(blank=True, null=True, verbose_name=_("Execution begin date"), help_text=_('format: mm/dd/yyyy'))
    execution_end_date = models.DateField(blank=True, null=True, verbose_name=_("Execution end date"), help_text=_('format: mm/dd/yyyy'))
    penalty_date = models.DateField(blank=True, null=True, verbose_name=_("Penalty date"), help_text=_('format: mm/dd/yyyy'))
    penalty_rate = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2, verbose_name=_("Penalty rate"))
    discount_conditions = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Discount conditions"))

    objects = InvoiceManager()

    class Meta:
        ordering = ['invoice_id']

    def __unicode__(self):
        return "<a href=\"%s\">%s</a>" % (reverse('invoice_detail', kwargs={'id' : self.id}), ugettext("invoice #%d") % (self.invoice_id))

    def isInvoiceIdValid(self):
        validator = MaxValueValidator(MAX_INVOICE_ID)
        try:
            validator(self.invoice_id)
        except:
            return False
        return True

    def isInvoiceIdUnique(self, owner):
        invoices = Invoice.objects.filter(owner=owner,
                                          invoice_id=self.invoice_id)
        if self.id:
            invoices = invoices.exclude(id=self.id)

        if len(invoices):
            return False

        return True

    def getNature(self):
        natures = self.invoice_rows.values_list('category', flat=True).order_by('category').distinct()
        result = []
        natures_dict = dict(ROW_CATEGORY)
        for nature in natures:
            result.append(unicode(natures_dict[nature]))

        return " & ".join(result)

    def save(self, force_insert=False, force_update=False, using=None, user=None):
        if not self.isInvoiceIdValid():
            raise InvalidInvoiceIdError(ugettext('Invoice id must be less than or equal to %d') % (MAX_INVOICE_ID))
        if not self.isInvoiceIdUnique(user):
            raise InvoiceIdNotUniqueError(ugettext("Invoice id must be unique"))
        super(Invoice, self).save(force_insert, force_update, using, user)

    def check_amounts(self):
        proposals = Proposal.objects.filter(invoice_rows__invoice=self).distinct()
        for proposal in proposals:
            remaining_amount = proposal.get_remaining_to_invoice(exclude_invoice=self)
            rows_amount = InvoiceRow.objects.filter(invoice=self,
                                                    proposal=proposal).aggregate(amount=Sum('amount'))['amount'] or 0
            if float(remaining_amount) < float(rows_amount):
                raise InvoiceRowAmountError(ugettext("Amounts invoiced can't be greater than proposals remaining amounts"))

        return True

    def get_vat(self):
        cursor = connection.cursor()
        cursor.execute('SELECT SUM(accounts_invoicerow.amount * accounts_invoicerow.vat_rate / 100) AS "vat" FROM "accounts_invoicerow" WHERE "accounts_invoicerow"."invoice_id" = %s', [self.id])
        row = cursor.fetchone()
        vat = row[0] or Decimal(0)
        vat = vat.quantize(Decimal(1)) if vat == vat.to_integral() else vat.normalize()
        return vat

    def amount_including_tax(self):
        return self.amount + self.get_vat()

    def to_pdf(self, user, response):
        filename = ugettext('invoice_%(invoice_id)d.pdf') % {'invoice_id': self.invoice_id}
        response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

        invoice_template = InvoiceTemplate(response, user)

        invoice_template.init_doc(ugettext('Invoice #%(invoice_id)d') % {'invoice_id': self.invoice_id})
        invoice_template.add_headers(self, self.customer, self.edition_date)
        invoice_template.add_title(_("INVOICE #%d") % (self.invoice_id))

        # proposal row list
        rows = self.invoice_rows.all()
        invoice_template.add_rows(rows)

        # total amount on the right side of footer
        right_block = invoice_template.get_total_amount(self.amount, rows)

        invoice_amount = self.amount
        invoice_amount = invoice_amount.quantize(Decimal(1)) if invoice_amount == invoice_amount.to_integral() else invoice_amount.normalize()
        left_block = [Paragraph(_("Payment date : %s") % (localize(self.payment_date)), InvoiceTemplate.styleN),
                      Paragraph(_("Penalty begins on : %s") % (localize(self.penalty_date) or ''), InvoiceTemplate.styleN),
                      Paragraph(_("Penalty rate : %s") % (localize(self.penalty_rate) or ''), InvoiceTemplate.styleN),
                      Paragraph(_("Discount conditions : %s") % (self.discount_conditions or ''), InvoiceTemplate.styleN)]
        if self.owner.get_profile().iban_bban:
            left_block.append(Spacer(invoice_template.doc.width, 0.2 * inch))
            left_block.append(Paragraph(_("IBAN/BBAN : %s") % (self.owner.get_profile().iban_bban), InvoiceTemplate.styleNSmall))
            if self.owner.get_profile().bic:
                left_block.append(Paragraph(_("BIC/SWIFT : %s") % (self.owner.get_profile().bic), InvoiceTemplate.styleNSmall))

        data = [[left_block,
                '',
                right_block], ]

        if self.execution_begin_date and self.execution_end_date:
            data[0][0].insert(1, Paragraph(_("Execution dates : %(begin_date)s to %(end_date)s") % {'begin_date': localize(self.execution_begin_date), 'end_date' : localize(self.execution_end_date)}, InvoiceTemplate.styleN))

        footer_table = Table(data, [4.5 * inch, 0.3 * inch, 2.5 * inch], [1 * inch])
        footer_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

        invoice_template.append_to_story(footer_table)

        invoice_template.build()

        return response

class InvoiceRowAmountError(Exception):
    pass

class InvoiceRow(Row):
    invoice = models.ForeignKey(Invoice, related_name="invoice_rows")
    proposal = models.ForeignKey(Proposal, related_name="invoice_rows", verbose_name=_('Proposal'), null=True, blank=True)
    balance_payments = models.BooleanField(verbose_name=_('Balance payments for the proposal'), help_text=_('"Balancing payments for the proposal" means there will be no future invoices for the selected proposal. Thus the amount remaining to invoice for this proposal will fall to zero and its state will be set to "balanced" when all invoices are paid.'))

    class Meta:
        ordering = ['id']

    def save(self, force_insert=False, force_update=False, using=None, user=None):
        super(InvoiceRow, self).save(force_insert, force_update, using, user)

def update_invoice_amount(sender, instance, created=None, **kwargs):
    row = instance
    invoice = row.invoice
    invoice.amount = invoice.invoice_rows.all().aggregate(sum=Sum('amount'))['sum'] or 0
    invoice.save(user=invoice.owner)

pre_save.connect(update_row_amount, sender=InvoiceRow)
post_save.connect(update_invoice_amount, sender=InvoiceRow)
post_delete.connect(update_invoice_amount, sender=InvoiceRow)
