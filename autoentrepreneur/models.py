# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from contact.models import Address
from django.db.models.signals import post_save
from project.models import Proposal, PROPOSAL_STATE_SENT, ProposalRow, PROPOSAL_STATE_DRAFT, PROPOSAL_STATE_ACCEPTED

from django.db.models.aggregates import Sum, Min
from accounts.models import Invoice, INVOICE_STATE_PAID, INVOICE_STATE_SENT, \
    InvoiceRow, INVOICE_STATE_EDITED
import datetime

AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC = 1
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC = 2
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC = 3
AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC = 4
AUTOENTREPRENEUR_ACTIVITY = ((AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, _('Product sale (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC, _('Provision of a service (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC, _('Provision of a service (BNC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC, _('Liberal profession (BNC)')))

AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY = 1
AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY = 2
AUTOENTREPRENEUR_PAYMENT_OPTION = ((AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY, _('Quaterly')),
                                   (AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY, _('Monthly')))

SALES_LIMIT = {AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC: 80300,
               AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC: 32100,
               AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC: 32100,
               AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC: 32100}

TAX_RATE_WITH_FREEING = {AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC: [4, 7, 10, 13],
                         AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC: [7.1, 12.4, 17.7, 23],
                         AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC: [7.6, 12.9, 18.2, 23.5],
                         AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC: [7.5, 11.4, 16, 20.5]
                         }

TAX_RATE_WITHOUT_FREEING = {AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC: [3, 6, 9, 12],
                            AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC: [5.4, 10.7, 16, 21.3],
                            AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC: [5.4, 10.7, 16, 21.3],
                            AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC: [5.3, 9.2, 13.8, 18.3]
                            }

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    company_name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Company name'))
    company_id = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Company id')) # SIRET for France
    bank_information = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Bank information'))
    address = models.ForeignKey(Address, verbose_name=_('Address'))
    activity = models.IntegerField(choices=AUTOENTREPRENEUR_ACTIVITY, blank=True, null=True, verbose_name=_('Activity'))
    creation_date = models.DateField(blank=True, null=True, verbose_name=_('Creation date'))
    creation_help = models.BooleanField(verbose_name=_('Creation help')) # accre
    freeing_tax_payment = models.BooleanField(verbose_name=_('Freeing tax payment')) # versement liberatoire
    payment_option = models.IntegerField(choices=AUTOENTREPRENEUR_PAYMENT_OPTION, blank=True, null=True, verbose_name=_('Payment option'))

    def get_sales_limit(self, year=None):
        today = datetime.date.today()
        if not year:
            year = today.year
        if self.activity:
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                return int(round(float(SALES_LIMIT[self.activity]) * worked_days.days / days_in_year.days))
            else:
                return SALES_LIMIT[self.activity]
        return 0

    def get_paid_sales(self, year=None):
        if not year:
            year = datetime.date.today().year
        amount_sum = Invoice.objects.filter(state=INVOICE_STATE_PAID,
                                            owner=self,
                                            paid_date__year=year).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_waiting_payments(self):
        amount_sum = Invoice.objects.filter(state=INVOICE_STATE_SENT,
                                            owner=self).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_to_be_invoiced(self):
        accepted_proposal_amount_sum = Proposal.objects.filter(state=PROPOSAL_STATE_ACCEPTED,
                                                               owner=self).extra(where=['project_proposal.ownedobject_ptr_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                                                 params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).aggregate(amount=Sum('amount'))
        invoicerows_to_exclude = InvoiceRow.objects.extra(where=['accounts_invoicerow.proposal_id NOT IN (SELECT proposal_id FROM accounts_invoicerow irow JOIN accounts_invoice i ON irow.invoice_id = i.ownedobject_ptr_id WHERE i.state IN (%s,%s) AND irow.balance_payments = %s)'],
                                                          params=[INVOICE_STATE_SENT, INVOICE_STATE_PAID, True]).exclude(invoice__state=INVOICE_STATE_EDITED).filter(owner=self).aggregate(amount=Sum('amount'))
        return (accepted_proposal_amount_sum['amount'] or 0) - (invoicerows_to_exclude['amount'] or 0)

    def get_late_invoices(self):
        late_invoices = Invoice.objects.filter(state=INVOICE_STATE_SENT,
                                               payment_date__lt=datetime.date.today(), owner=self)
        return late_invoices

    def get_invoices_to_send(self):
        invoices_to_send = Invoice.objects.filter(state=INVOICE_STATE_EDITED,
                                                  edition_date__lte=datetime.date.today(),
                                                  owner=self)
        return invoices_to_send


    def get_potential_sales(self):
        amount_sum = Proposal.objects.filter(state__lte=PROPOSAL_STATE_SENT,
                                             owner=self).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_proposals_to_send(self):
        proposals = Proposal.objects.filter(state=PROPOSAL_STATE_DRAFT,
                                            owner=self)
        return proposals

    def get_potential_duration(self):
        quantity_sum = ProposalRow.objects.filter(proposal__state__lte=PROPOSAL_STATE_SENT,
                                                  owner=self).aggregate(quantity=Sum('quantity'))
        return quantity_sum['quantity'] or 0

    def get_period_for_tax(self, reference_date=None):
        begin_date = end_date = None
        current_date = reference_date or datetime.date.today()

        if self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY:
            if current_date.month == 1:
                begin_date = datetime.date(current_date.year - 1, 12, 1)
                end_date = datetime.date(current_date.year - 1, 12, 31)
            else:
                begin_date = datetime.date(current_date.year, current_date.month - 1, 1)
                end_date = datetime.date(current_date.year, current_date.month - 1, 31)

            year = self.creation_date.year
            if self.creation_date.month >= 10:
                year = self.creation_date.year + 1
            first_date = datetime.date(year,
                                       (self.creation_date.month + 4) % 12 or 12,
                                       1) - datetime.timedelta(1)

            if begin_date < first_date:
                begin_date = self.creation_date

        elif self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY:
            if self.creation_date > current_date - datetime.timedelta(90):
                current_date = current_date + datetime.timedelta(90)
            if current_date.month == 1:
                begin_date = datetime.date(current_date.year - 1, 10, 1)
                end_date = datetime.date(current_date.year - 1, 12, 31)
            elif current_date.month <= 4:
                begin_date = datetime.date(current_date.year, 1, 1)
                end_date = datetime.date(current_date.year, 3, 31)
            elif current_date.month <= 7:
                begin_date = datetime.date(current_date.year, 4, 1)
                end_date = datetime.date(current_date.year, 6, 30)
            elif current_date.month <= 10:
                begin_date = datetime.date(current_date.year, 7, 1)
                end_date = datetime.date(current_date.year, 9, 30)
            else:
                begin_date = datetime.date(current_date.year, 10, 1)
                end_date = datetime.date(current_date.year, 12, 31)
            if self.creation_date > begin_date - datetime.timedelta(90):
                    begin_date = self.creation_date

        return begin_date, end_date

    def get_paid_sales_for_period(self, begin_date, end_date):
        if not begin_date or not end_date:
            return 0
        amount_sum = Invoice.objects.filter(state=INVOICE_STATE_PAID,
                                            owner=self,
                                            paid_date__gte=begin_date,
                                            paid_date__lte=end_date).aggregate(sales=Sum('amount'))
        return amount_sum['sales'] or 0

    def get_tax_rate(self, reference_date=None):
        tax_rate = 0
        if not self.activity:
            return tax_rate
        today = reference_date or datetime.date.today()

        if self.creation_help:
            year = self.creation_date.year + 1
            month = (self.creation_date.month - 1) // 3 * 3 + 1
            first_period_end_date = datetime.date(year, month, 1) - datetime.timedelta(1)
            second_period_end_date = datetime.date(first_period_end_date.year + 1,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            third_period_end_date = datetime.date(first_period_end_date.year + 2,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            if today <= first_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][0]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][0]
            elif today <= second_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][1]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][1]
            elif today <= third_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][2]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][2]

            else:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]
        else:
            if self.freeing_tax_payment:
                tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
            else:
                tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]

        return tax_rate

    def get_pay_date(self, end_date=None):
        pay_date = None
        if end_date:
            year = end_date.year
            if end_date.month == 12:
                year = year + 1
            pay_date = datetime.date(year,
                                     (end_date.month + 2) % 12 or 12,
                                     1) - datetime.timedelta(1)
        return pay_date


    def get_first_invoice_paid_date(self):
        return Invoice.objects.aggregate(min_date=Min('paid_date'))['min_date']

    def get_paid_invoices(self, begin_date=None):
        if not begin_date:
            return Invoice.objects.filter(state=INVOICE_STATE_PAID,
                                          owner=self,
                                          paid_date__year=datetime.date.today().year).order_by('paid_date')
        else:
            return Invoice.objects.filter(state=INVOICE_STATE_PAID,
                                          owner=self,
                                          paid_date__lte=datetime.date.today(),
                                          paid_date__gte=begin_date).order_by('paid_date')

    def get_waiting_invoices(self):
            return Invoice.objects.filter(state__lte=INVOICE_STATE_SENT,
                                          owner=self).order_by('payment_date')


def user_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            profile = UserProfile.objects.get(user=instance)
        except:
            address = Address()
            address.save(user=instance)
            profile = UserProfile()
            profile.user = instance
            profile.address = address
            profile.save()

post_save.connect(user_post_save, sender=User)
