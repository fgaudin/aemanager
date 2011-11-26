# -*- coding: utf-8 -*-

import unicodedata
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle

from decimal import Decimal
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from contact.models import Contact
from core.models import OwnedObject
from django.db.models.signals import post_save, pre_save
from django.utils.formats import localize
from django.db.models.aggregates import Sum
from core.templatetags.htmltags import to_html
from django.conf import settings
import ho.pisa as pisa
from django.core.files.storage import FileSystemStorage
from django.db.models.query_utils import Q
from project.utils.pdf import ProposalTemplate

store = FileSystemStorage(location=settings.FILE_UPLOAD_DIR)

def contract_upload_to_handler(instance, filename):
        return "%s/contract/%s" % (instance.owner.get_profile().uuid, unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore'))

class Contract(OwnedObject):
    customer = models.ForeignKey(Contact, verbose_name=_('Customer'), related_name="contracts")
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    contract_file = models.FileField(upload_to=contract_upload_to_handler, null=True, blank=True, storage=store, verbose_name=_('Uploaded contract'), help_text=_('max. %(FILE_MAX_SIZE)s') % {'FILE_MAX_SIZE': settings.FILE_MAX_SIZE})
    content = models.TextField(verbose_name=_('Content'), null=True, blank=True)
    update_date = models.DateField(verbose_name=_('Update date'), help_text=_('format: mm/dd/yyyy'))

    def __unicode__(self):
        return self.title

    @staticmethod
    def get_substitution_map():
        substitution_map = {ugettext('customer'): '',
                            ugettext('customer_legal_form'): '',
                            ugettext('customer_street'): '',
                            ugettext('customer_zipcode'): '',
                            ugettext('customer_city'): '',
                            ugettext('customer_country'): '',
                            ugettext('customer_company_id'): '',
                            ugettext('customer_representative'): '',
                            ugettext('customer_representative_function'): '',
                            ugettext('firstname'): '',
                            ugettext('lastname'): '',
                            ugettext('street'): '',
                            ugettext('zipcode'): '',
                            ugettext('city'): '',
                            ugettext('country'): '',
                            ugettext('company_id'): '',
                            }

        return substitution_map

    def to_pdf(self, user, response):
        css_file = open("%s%s" % (settings.MEDIA_ROOT, "/css/pisa.css"), 'r')
        css = css_file.read()

        substitution_map = Contract.get_substitution_map()

        substitution_map[ugettext('customer')] = unicode(self.customer)
        substitution_map[ugettext('customer_legal_form')] = self.customer.legal_form
        substitution_map[ugettext('customer_street')] = self.customer.address.street
        substitution_map[ugettext('customer_zipcode')] = self.customer.address.zipcode
        substitution_map[ugettext('customer_city')] = self.customer.address.city
        substitution_map[ugettext('customer_country')] = unicode(self.customer.address.country)
        substitution_map[ugettext('customer_company_id')] = self.customer.company_id
        substitution_map[ugettext('customer_representative')] = self.customer.representative
        substitution_map[ugettext('customer_representative_function')] = self.customer.representative_function
        substitution_map[ugettext('firstname')] = user.first_name
        substitution_map[ugettext('lastname')] = user.last_name
        substitution_map[ugettext('street')] = user.get_profile().address.street
        substitution_map[ugettext('zipcode')] = user.get_profile().address.zipcode
        substitution_map[ugettext('city')] = user.get_profile().address.city
        substitution_map[ugettext('country')] = unicode(user.get_profile().address.country)
        substitution_map[ugettext('company_id')] = user.get_profile().company_id

        contract_content = "<h1>%s</h1>%s" % (self.title, self.content.replace('&nbsp;', ' '))

        for tag, value in substitution_map.items():
            contract_content = contract_content.replace('{{ %s }}' % (tag), value)

        pdf = pisa.pisaDocument(to_html(contract_content),
                                response,
                                default_css=css)
        return response

PROJECT_STATE_PROSPECT = 1
PROJECT_STATE_PROPOSAL_SENT = 2
PROJECT_STATE_PROPOSAL_ACCEPTED = 3
PROJECT_STATE_STARTED = 4
PROJECT_STATE_FINISHED = 5
PROJECT_STATE_CANCELED = 6
PROJECT_STATE = ((PROJECT_STATE_PROSPECT, _('Prospect')),
                 (PROJECT_STATE_PROPOSAL_SENT, _('Proposal sent')),
                 (PROJECT_STATE_PROPOSAL_ACCEPTED, _('Proposal accepted')),
                 (PROJECT_STATE_STARTED, _('Started')),
                 (PROJECT_STATE_FINISHED, _('Finished')),
                 (PROJECT_STATE_CANCELED, _('Canceled')),)

class Project(OwnedObject):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    customer = models.ForeignKey(Contact, verbose_name=_('Customer'))
    state = models.IntegerField(choices=PROJECT_STATE, default=PROJECT_STATE_PROSPECT, verbose_name=_('State'), db_index=True)

    def __unicode__(self):
        return self.name

    def is_proposal_accepted(self):
        if self.state >= PROJECT_STATE_PROPOSAL_ACCEPTED:
            return True
        return False

class ProposalAmountError(Exception):
    pass

PROPOSAL_STATE_DRAFT = 1
PROPOSAL_STATE_SENT = 2
PROPOSAL_STATE_ACCEPTED = 3
PROPOSAL_STATE_BALANCED = 4
PROPOSAL_STATE_REFUSED = 5
PROPOSAL_STATE = ((PROPOSAL_STATE_DRAFT, _('Draft')),
                  (PROPOSAL_STATE_SENT, _('Sent')),
                  (PROPOSAL_STATE_ACCEPTED, _('Accepted')),
                  (PROPOSAL_STATE_BALANCED, _('Balanced')),
                  (PROPOSAL_STATE_REFUSED, _('Refused')))

PAYMENT_DELAY_30_DAYS = 1
PAYMENT_DELAY_60_DAYS = 2
PAYMENT_DELAY_45_DAYS_END_OF_MONTH = 3
PAYMENT_DELAY_END_OF_MONTH_PLUS_45_DAYS = 4
PAYMENT_DELAY_OTHER = 5
PAYMENT_DELAY = ((PAYMENT_DELAY_30_DAYS, _('30 days')),
                 (PAYMENT_DELAY_60_DAYS, _('60 days')),
                 (PAYMENT_DELAY_45_DAYS_END_OF_MONTH, _('45 days end of month')),
                 (PAYMENT_DELAY_END_OF_MONTH_PLUS_45_DAYS, _('End of month + 45 days')),
                 (PAYMENT_DELAY_OTHER, _('Other')))

PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH = 1
PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH_PLUS_DELAY = 2
PAYMENT_DELAY_TYPE_OTHER = ((PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH, _('End of month')),
                            (PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH_PLUS_DELAY, _('End of month + delay')))

class ProposalManager(models.Manager):
    def get_potential_sales(self, owner):
        amount_sum = self.filter(state__lte=PROPOSAL_STATE_SENT,
                                 owner=owner).exclude(project__state__gte=PROJECT_STATE_FINISHED).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_proposals_to_send(self, owner):
        proposals = self.filter(state=PROPOSAL_STATE_DRAFT,
                                owner=owner).exclude(project__state__gte=PROJECT_STATE_FINISHED)
        return proposals

    def get_potential_duration(self, owner):
        quantity_sum = ProposalRow.objects.filter(proposal__state__lte=PROPOSAL_STATE_SENT,
                                                  owner=owner).exclude(proposal__project__state__gte=PROJECT_STATE_FINISHED).aggregate(quantity=Sum('quantity'))
        return quantity_sum['quantity'] or 0

    def get_proposals_for_invoice(self, customer, user, invoice=None):
        filter = Q(project__customer=customer,
                   state=PROPOSAL_STATE_ACCEPTED,
                   owner=user)
        if invoice:
            filter = filter | Q(invoice_rows__invoice=invoice,
                                owner=user)

        return self.filter(filter).distinct()

def proposal_upload_to_handler(instance, filename):
        return "%s/proposal/%s" % (instance.owner.get_profile().uuid, unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore'))

class Proposal(OwnedObject):
    project = models.ForeignKey(Project)
    reference = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Reference'))
    state = models.IntegerField(choices=PROPOSAL_STATE, default=PROPOSAL_STATE_DRAFT, verbose_name=_('State'), db_index=True)
    amount = models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=2, verbose_name=_('Amount'))
    begin_date = models.DateField(blank=True, null=True, verbose_name=_('Begin date'), help_text=_('format: mm/dd/yyyy'))
    end_date = models.DateField(blank=True, null=True, verbose_name=_('End date'), help_text=_('format: mm/dd/yyyy'))
    contract_content = models.TextField(blank=True, default="", verbose_name=_('Contract'))
    update_date = models.DateField(verbose_name=_('Update date'), help_text=_('format: mm/dd/yyyy'))
    expiration_date = models.DateField(blank=True, null=True, verbose_name=_('Expiration date'), help_text=_('format: mm/dd/yyyy'))
    payment_delay = models.IntegerField(choices=PAYMENT_DELAY, default=PAYMENT_DELAY_30_DAYS, verbose_name=_('Payment delay'), help_text=_("Can't be more than 60 days or 45 days end of month."))
    payment_delay_other = models.IntegerField(blank=True, null=True)
    payment_delay_type_other = models.IntegerField(choices=PAYMENT_DELAY_TYPE_OTHER, blank=True, null=True)
    contract_file = models.FileField(upload_to=proposal_upload_to_handler, null=True, blank=True, storage=store, verbose_name=_('Uploaded contract'), help_text=_('max. %(FILE_MAX_SIZE)s') % {'FILE_MAX_SIZE': settings.FILE_MAX_SIZE})

    objects = ProposalManager()

    class Meta:
        ordering = ['begin_date', 'update_date']

    def __unicode__(self):
        if self.begin_date and self.end_date:
            return _('Proposal %(reference)s from %(begin_date)s to %(end_date)s for %(project)s') % {'reference': self.reference,
                                                                                                      'begin_date': localize(self.begin_date),
                                                                                                      'end_date': localize(self.end_date),
                                                                                                      'project' : self.project}
        else:
            return _('Proposal %(reference)s for %(project)s') % {'reference': self.reference,
                                                                                                      'project' : self.project}

    def is_accepted(self):
        return self.state == PROPOSAL_STATE_ACCEPTED or self.state == PROPOSAL_STATE_BALANCED

    def can_be_converted_to_invoice(self):
        return self.state == PROPOSAL_STATE_ACCEPTED and self.get_remaining_to_invoice() > 0

    def get_next_states(self):
        if self.state == PROPOSAL_STATE_DRAFT:
            return (PROPOSAL_STATE[PROPOSAL_STATE_SENT - 1],)
        elif self.state == PROPOSAL_STATE_SENT:
            return (PROPOSAL_STATE[PROPOSAL_STATE_ACCEPTED - 1], PROPOSAL_STATE[PROPOSAL_STATE_REFUSED - 1])

        return ()

    def get_remaining_to_invoice(self, exclude_invoice=None):
        balancing_invoices = self.invoice_rows.filter(balance_payments=True)
        has_balancing_invoice = balancing_invoices.count()
        if not exclude_invoice and has_balancing_invoice:
            return 0

        invoice_rows = self.invoice_rows.filter(invoice__state__gte=1)
        if exclude_invoice:
            invoice_rows = invoice_rows.exclude(invoice=exclude_invoice)
        invoice_amount = invoice_rows.aggregate(amount=Sum('amount'))
        return self.amount - (invoice_amount['amount'] or 0)

    def get_payment_delay(self):
        if self.payment_delay <> PAYMENT_DELAY_OTHER:
            return self.get_payment_delay_display()
        else:
            if self.payment_delay_type_other == PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH:
                return _('%(days)d days end of month') % {'days': self.payment_delay_other}
            elif self.payment_delay_type_other == PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH_PLUS_DELAY:
                return _('end of month + %(days)d days') % {'days': self.payment_delay_other}
            else:
                return _('%(days)d days') % {'days': self.payment_delay_other}

    def update_amount(self):
        """
        Set amount equals to sum of proposal rows if none
        """
        amount = 0
        for row in self.proposal_rows.all():
            amount = amount + row.quantity * row.unit_price

        self.amount = amount
        invoicerow_sum = float(self.invoice_rows.all().aggregate(sum=Sum('amount'))['sum'] or 0)
        if float(self.amount) < invoicerow_sum :
            raise ProposalAmountError(ugettext("Proposal amount can't be less than sum of invoices"))
        self.save(user=self.owner)

    def to_pdf(self, user, response):
        """
        Generate a PDF file for the proposal
        """
        filename = ugettext('proposal_%(id)d.pdf') % {'id': self.id}
        response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

        proposal_template = ProposalTemplate(response, user)

        proposal_template.init_doc(ugettext('Proposal %(reference)s') % {'reference': self.reference})
        proposal_template.add_headers(self, self.project.customer, self.update_date)
        proposal_template.add_title(_("PROPOSAL %s") % (self.reference))

        # proposal row list
        rows = self.proposal_rows.all()
        proposal_template.add_rows(rows)

        # total amount on the right side of footer
        right_block = proposal_template.get_total_amount(self.amount, rows)

        # left side of footer
        data = [[[Paragraph(_("Proposal valid through : %s") % (localize(self.expiration_date) or ''), ProposalTemplate.styleN),
                  Paragraph(_("Payment delay : %s") % (self.get_payment_delay()), ProposalTemplate.styleN)],
                '',
                right_block], ]

        if self.begin_date and self.end_date:
            data[0][0].append(Paragraph(_("Execution dates : %(begin_date)s to %(end_date)s") % {'begin_date': localize(self.begin_date), 'end_date' : localize(self.end_date)}, ProposalTemplate.styleN))

        footer_table = Table(data, [4.5 * inch, 0.3 * inch, 2.5 * inch], [1 * inch])
        footer_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

        proposal_template.append_to_story(footer_table)

        proposal_template.build()

        return response

    @staticmethod
    def get_substitution_map():
        substitution_map = {ugettext('reference'): '',
                            ugettext('payment_delay'): '',
                            ugettext('customer'): '',
                            ugettext('customer_legal_form'): '',
                            ugettext('customer_street'): '',
                            ugettext('customer_zipcode'): '',
                            ugettext('customer_city'): '',
                            ugettext('customer_country'): '',
                            ugettext('customer_company_id'): '',
                            ugettext('customer_representative'): '',
                            ugettext('customer_representative_function'): '',
                            ugettext('firstname'): '',
                            ugettext('lastname'): '',
                            ugettext('street'): '',
                            ugettext('zipcode'): '',
                            ugettext('city'): '',
                            ugettext('country'): '',
                            ugettext('company_id'): '',
                            }

        return substitution_map

    def contract_to_pdf(self, user, response):
        css_file = open("%s%s" % (settings.MEDIA_ROOT, "/css/pisa.css"), 'r')
        css = css_file.read()

        substitution_map = Proposal.get_substitution_map()

        substitution_map[ugettext('reference')] = unicode(self.reference)
        substitution_map[ugettext('payment_delay')] = unicode(self.get_payment_delay())
        substitution_map[ugettext('customer')] = unicode(self.project.customer)
        substitution_map[ugettext('customer_legal_form')] = self.project.customer.legal_form
        substitution_map[ugettext('customer_street')] = self.project.customer.address.street
        substitution_map[ugettext('customer_zipcode')] = self.project.customer.address.zipcode
        substitution_map[ugettext('customer_city')] = self.project.customer.address.city
        substitution_map[ugettext('customer_country')] = unicode(self.project.customer.address.country)
        substitution_map[ugettext('customer_company_id')] = self.project.customer.company_id
        substitution_map[ugettext('customer_representative')] = self.project.customer.representative
        substitution_map[ugettext('customer_representative_function')] = self.project.customer.representative_function
        substitution_map[ugettext('firstname')] = user.first_name
        substitution_map[ugettext('lastname')] = user.last_name
        substitution_map[ugettext('street')] = user.get_profile().address.street
        substitution_map[ugettext('zipcode')] = user.get_profile().address.zipcode
        substitution_map[ugettext('city')] = user.get_profile().address.city
        substitution_map[ugettext('country')] = unicode(user.get_profile().address.country)
        substitution_map[ugettext('company_id')] = user.get_profile().company_id

        contract_content = self.contract_content.replace('&nbsp;', ' ')

        for tag, value in substitution_map.items():
            contract_content = contract_content.replace('{{ %s }}' % (tag), value)

        pdf = pisa.pisaDocument(to_html(contract_content),
                                response,
                                default_css=css)
        return response

def update_project_state(sender, instance, created, **kwargs):
    proposal = instance
    project = proposal.project
    if project.state != PROJECT_STATE_STARTED:
        if proposal.state == PROPOSAL_STATE_SENT:
            project.state = PROJECT_STATE_PROPOSAL_SENT
        elif proposal.state == PROPOSAL_STATE_ACCEPTED:
            project.state = PROJECT_STATE_PROPOSAL_ACCEPTED

    try:
        project.save(user=proposal.owner)
    except:
        pass

post_save.connect(update_project_state, sender=Proposal)

ROW_CATEGORY_SERVICE = 1
ROW_CATEGORY_PRODUCT = 2
ROW_CATEGORY = ((ROW_CATEGORY_SERVICE, _('Service')),
                (ROW_CATEGORY_PRODUCT, _('Product')))

VAT_RATES_19_6 = Decimal('19.6')
VAT_RATES_5_5 = Decimal('5.5')
VAT_RATES_2_1 = Decimal('2.1')
VAT_RATES = ((VAT_RATES_19_6, _('%s%%') % (localize(VAT_RATES_19_6))),
             (VAT_RATES_5_5, _('%s%%') % (localize(VAT_RATES_5_5))),
             (VAT_RATES_2_1, _('%s%%') % (localize(VAT_RATES_2_1))),)

class Row(OwnedObject):
    label = models.CharField(max_length=255, verbose_name=_('Label'))
    category = models.IntegerField(choices=ROW_CATEGORY, verbose_name=_('Category'))
    quantity = models.DecimalField(max_digits=5, decimal_places=1, verbose_name=_('Quantity'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Unit price'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name=_('Amount'))
    vat_rate = models.DecimalField(choices=VAT_RATES, decimal_places=1, max_digits=4, verbose_name=_('Vat'), blank=True, null=True)
    detail = models.TextField(verbose_name=_('Detail'), blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ['id']

def update_row_amount(sender, instance, **kwargs):
    row = instance
    row.amount = Decimal(row.quantity) * Decimal(row.unit_price)

class ProposalRow(Row):
    proposal = models.ForeignKey(Proposal, related_name="proposal_rows")

def update_proposal_amount(sender, instance, created, **kwargs):
    row = instance
    proposal = row.proposal
    proposal.amount = proposal.proposal_rows.all().aggregate(sum=Sum('amount'))['sum'] or 0
    proposal.save(user=proposal.owner)

pre_save.connect(update_row_amount, sender=ProposalRow)
post_save.connect(update_proposal_amount, sender=ProposalRow)
