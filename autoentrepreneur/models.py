# -*- coding: utf-8 -*-
import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from contact.models import Address
from django.db.models.signals import post_save
from django.db.models.aggregates import Max, Count
from core.models import OwnedObject
from bugtracker.models import Issue
from django.core.mail import send_mail
from django.contrib.sites.models import Site
import datetime
from django.conf import settings
from registration.signals import user_registered
from django.core.files.storage import FileSystemStorage
import unicodedata
from accounts.models import Invoice

AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC = 1
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC = 2
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC = 3
AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC = 4
AUTOENTREPRENEUR_ACTIVITY = ((AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, _('Product sale (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC, _('Provision of a service (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC, _('Provision of a service (BNC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC, _('Liberal profession (BNC)')))

class SalesLimit(models.Model):
    year = models.IntegerField(verbose_name=_('Year'))
    activity = models.IntegerField(choices=AUTOENTREPRENEUR_ACTIVITY,
                                   verbose_name=_('Activity'))
    limit = models.IntegerField(verbose_name=_('Limit'))
    limit2 = models.IntegerField(verbose_name=_('Limit 2'))

SUBSCRIPTION_STATE_NOT_PAID = 1
SUBSCRIPTION_STATE_PAID = 2
SUBSCRIPTION_STATE_TRIAL = 3
SUBSCRIPTION_STATE_FREE = 4
SUBSCRIPTION_STATE = ((SUBSCRIPTION_STATE_NOT_PAID, _('Not paid')),
                      (SUBSCRIPTION_STATE_PAID, _('Paid')),
                      (SUBSCRIPTION_STATE_TRIAL, _('Trial')),
                      (SUBSCRIPTION_STATE_FREE, _('Free')))

class SubscriptionManager(models.Manager):
    def get_not_paid_subscription(self, user):
        return self.filter(state=SUBSCRIPTION_STATE_NOT_PAID,
                           owner=user).order_by('-expiration_date')

    def get_users_with_paid_subscription(self):
        return self.filter(expiration_date__gte=datetime.date.today(),
                           owner__is_active=True,
                           state=SUBSCRIPTION_STATE_PAID).values('owner__email',
                                                                 'owner__first_name',
                                                                 'owner__last_name').distinct()

    def get_users_with_trial_subscription(self):
        return self.filter(owner__is_active=True).values('owner').annotate(sub_count=Count('id'),
                                                                           state=Max('state'),
                                                                           date=Max('expiration_date')).values('owner__email',
                                                                                                               'owner__first_name',
                                                                                                               'owner__last_name').filter(sub_count=1,
                                                                                                                                          date__gte=datetime.date.today(),
                                                                                                                                          state=SUBSCRIPTION_STATE_TRIAL).distinct()

    def get_users_with_expired_subscription(self):
        return self.filter(owner__is_active=True).values('owner').annotate(max_date=Max('expiration_date')).values('owner__email',
                                                                                                                   'owner__first_name',
                                                                                                                   'owner__last_name').filter(max_date__lt=datetime.date.today()).distinct()

    def get_users_with_paid_subscription_expiring_in(self, days=30):
        return self.filter(expiration_date=datetime.date.today() + datetime.timedelta(days),
                           owner__is_active=True,
                           state=SUBSCRIPTION_STATE_PAID).values('owner__email',
                                                                 'owner__first_name',
                                                                 'owner__last_name').distinct().order_by('owner__email')

    def get_users_with_trial_subscription_expiring_in(self, days=7):
        return self.all().values('owner').annotate(sub_count=Count('id'),
                                                   state=Max('state'),
                                                   date=Max('expiration_date')).values('owner__email',
                                                                                       'owner__first_name',
                                                                                       'owner__last_name').filter(sub_count=1,
                                                                                                                  date=datetime.date.today() + datetime.timedelta(days),
                                                                                                                  state=SUBSCRIPTION_STATE_TRIAL).distinct().order_by('owner__email')

    def get_users_with_subscription_expired_for(self, days):
        return self.filter(owner__is_active=True).exclude(state=SUBSCRIPTION_STATE_FREE)\
                   .values_list('owner', flat=True)\
                   .annotate(max_date=Max('expiration_date'))\
                   .filter(max_date__lte=datetime.date.today() - datetime.timedelta(days)).distinct()

class Subscription(OwnedObject):
    state = models.IntegerField(choices=SUBSCRIPTION_STATE, verbose_name=_('State'), db_index=True)
    expiration_date = models.DateField(verbose_name=_('Expiration date'), help_text=_('format: mm/dd/yyyy'), db_index=True)
    transaction_id = models.CharField(verbose_name=_('Transaction id'), unique=True, max_length=50)
    error_message = models.CharField(verbose_name=_('Error message'), max_length=150, null=True, blank=True)

    objects = SubscriptionManager()

    def __unicode__(self):
        return "%s - %s - %s" % (self.owner.username,
                                 self.get_state_display(),
                                 self.expiration_date)

AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY = 1
AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY = 2
AUTOENTREPRENEUR_PAYMENT_OPTION = ((AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY, _('Quaterly')),
                                   (AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY, _('Monthly')))

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

AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_TRADER = 1
AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN = 2
AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL = 3
AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY = ((AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_TRADER, _('Trader')),
                                          (AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN, _('Craftsman')),
                                          (AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL, _('Liberal profession')))

AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN_ALSACE = 4
PROFESSIONAL_FORMATION_TAX_RATE = {AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_TRADER: 0.1,
                                   AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN: 0.3,
                                   AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN_ALSACE: 0.17,
                                   AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL: 0.2}

store = FileSystemStorage(location=settings.FILE_UPLOAD_DIR)

def logo_upload_to_handler(instance, filename):
        return "%s/logo/%s" % (instance.user.username, unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore'))

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    phonenumber = models.CharField(max_length=20, blank=True, default='', verbose_name=_('Phone number'), help_text=_('will appear on your proposals if set'))
    professional_email = models.EmailField(blank=True, default='', verbose_name=_('Professional email'), help_text=_('will appear on your proposals if set'))
    company_name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Company name'))
    company_id = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Company id')) # SIRET for France
    address = models.ForeignKey(Address, verbose_name=_('Address'))
    activity = models.IntegerField(choices=AUTOENTREPRENEUR_ACTIVITY, blank=True, null=True, verbose_name=_('Activity'))
    professional_category = models.IntegerField(choices=AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY, blank=True, null=True, verbose_name=_('Professional category'))
    creation_date = models.DateField(blank=True, null=True, verbose_name=_('Creation date'), help_text=_('format: mm/dd/yyyy'))
    creation_help = models.BooleanField(verbose_name=_('Creation help')) # accre
    freeing_tax_payment = models.BooleanField(verbose_name=_('Freeing tax payment')) # versement liberatoire
    payment_option = models.IntegerField(choices=AUTOENTREPRENEUR_PAYMENT_OPTION, blank=True, null=True, verbose_name=_('Payment option'))
    unregister_datetime = models.DateTimeField(verbose_name=_('Unregister date'), null=True, blank=True)
    iban_bban = models.CharField(max_length=34, blank=True, default='', verbose_name=_('IBAN/BBAN'), help_text=_('will appear on your invoices if set'))
    bic = models.CharField(max_length=11, blank=True, default='', verbose_name=_('BIC/SWIFT'), help_text=_('will appear on your invoices if set'))
    logo_file = models.FileField(upload_to=logo_upload_to_handler, null=True, blank=True, storage=store, verbose_name=_('Custom header'), help_text=_('will appear in place of your personnal informations on proposals and invoices. Maximum width and height: 252x137'))

    def __unicode__(self):
        return self.user.__unicode__()

    def unregister(self):
        """
        marked as to be deleted
        will be deleted by command delete_unregistered_users
        """
        self.unregister_datetime = datetime.datetime.now()
        self.save()
        self.user.is_active = False
        self.user.save()
        subject = _("You've just unregistered from %(site)s") % {'site': Site.objects.get_current().name}
        message = _("You have left the site and your data will been deleted in %(account_delete_delay)s days. "
                    "If you change your mind please contact us at %(contact_mail)s.\n\n"
                    "Our service is continually evolving and if it does not meet your "
                    "needs today, please come back to test later.") % {'account_delete_delay':settings.ACCOUNT_UNREGISTER_DAYS,
                                                                       'contact_mail': settings.MANAGERS[0][1]}
        message = message + "\n\n"
        message = message + _("The %(site_name)s team") % {'site_name': Site.objects.get_current().name}

        from_email = settings.DEFAULT_FROM_EMAIL
        user_email = self.user.email
        recipient_list = [user_email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)



    def settings_defined(self):
        settings_defined = False
        if self.user.first_name \
            and self.user.last_name \
            and self.company_id \
            and self.address.street \
            and self.address.zipcode \
            and self.address.city \
            and self.activity \
            and self.professional_category \
            and self.creation_date \
            and self.payment_option:

            settings_defined = True

        return settings_defined

    def is_allowed(self):
        try:
            Subscription.objects.get(owner=self.user,
                                     state__in=[SUBSCRIPTION_STATE_FREE])
            return True
        except:
            pass
        if Subscription.objects.filter(owner=self.user,
                                       state__in=[SUBSCRIPTION_STATE_PAID, SUBSCRIPTION_STATE_TRIAL],
                                       expiration_date__gte=datetime.date.today()).count():
            return True

        return False

    def unread_message_count(self):
        return Issue.objects.unread_messages(self.user)

    def get_next_expiration_date(self):
        last_valid_expiration_date = Subscription.objects.filter(owner=self.user,
                                                                 state__in=[SUBSCRIPTION_STATE_PAID,
                                                                            SUBSCRIPTION_STATE_TRIAL]).aggregate(last_date=Max('expiration_date'))
        today = datetime.date.today()
        ref_date = last_valid_expiration_date['last_date']
        if not ref_date or ref_date < today:
            ref_date = today

        next_date = None
        try:
            next_date = datetime.date(ref_date.year + 1, ref_date.month, ref_date.day)
        except:
            # case of February 29th
            next_date = datetime.date(ref_date.year + 1, 3, 1)

        return next_date

    def get_last_subscription(self):
        subscription = Subscription.objects.filter(owner=self.user).exclude(state=SUBSCRIPTION_STATE_NOT_PAID).order_by('-expiration_date')[0]
        return subscription

    def get_sales_limit(self, year=None):
        today = datetime.date.today()
        limit = 0
        if not year:
            year = today.year
        if self.activity:
            limit = SalesLimit.objects.get(year=year, activity=self.activity).limit
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                limit = int(round(float(limit) * worked_days.days / days_in_year.days))
        return limit

    def get_sales_limit2(self, year=None):
        today = datetime.date.today()
        limit = 0
        if not year:
            year = today.year
        if self.activity:
            limit = SalesLimit.objects.get(year=year, activity=self.activity).limit2
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                limit = int(round(float(limit) * worked_days.days / days_in_year.days))
        return limit

    def get_service_sales_limit(self, year=None):
        today = datetime.date.today()
        service_limit = 0
        if not year:
            year = today.year
        if self.activity == AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC:
            service_limit = SalesLimit.objects.get(year=year, activity=AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC).limit
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                service_limit = int(round(float(service_limit) * worked_days.days / days_in_year.days))
        return service_limit

    def get_quarter(self, date):
        return ((date.month + 2) // 3, date.year)

    def get_next_quarter(self, quarter, year):
        next_quarter = quarter % 4 + 1
        next_year = year
        if quarter == 4:
            next_year = next_year + 1
        return (next_quarter, next_year)

    def get_first_period_payment_date(self):
        if self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY:
            first_quarter = self.get_quarter(self.creation_date)
            second_quarter = self.get_next_quarter(first_quarter[0], first_quarter[1])
            third_quarter = self.get_next_quarter(second_quarter[0], second_quarter[1])
            payment_date = datetime.date(third_quarter[1], third_quarter[0] * 3 - 1, 1) - datetime.timedelta(1)
        else:
            payment_date = datetime.date(self.creation_date.year + self.creation_date.month // 9,
                                         (self.creation_date.month + 3) % 12 + 1,
                                         1)
        return payment_date

    def get_period_for_tax(self, reference_date=None):
        begin_date = end_date = None
        current_date = reference_date or datetime.date.today()
        first_period = False
        first_payment_date = self.get_first_period_payment_date()
        if current_date <= first_payment_date:
            current_date = first_payment_date
            first_period = True

        if self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY:
            if current_date.month == 1:
                begin_date = datetime.date(current_date.year - 1, 12, 1)
                end_date = datetime.date(current_date.year - 1, 12, 31)
            else:
                begin_date = datetime.date(current_date.year, current_date.month - 1, 1)
                end_date = datetime.date(current_date.year, current_date.month, 1) - datetime.timedelta(1)

        elif self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY:
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
        if first_period:
            begin_date = self.creation_date

        return begin_date, end_date

    def get_professional_training_tax_rate(self):
        tax_rate = 0
        if self.professional_category == AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_TRADER:
            tax_rate = PROFESSIONAL_FORMATION_TAX_RATE[AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_TRADER]
        elif self.professional_category == AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN:
            if len(self.address.zipcode) == 5 and self.address.zipcode[:2] in ['67', '68']:
                tax_rate = PROFESSIONAL_FORMATION_TAX_RATE[AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN_ALSACE]
            else:
                tax_rate = PROFESSIONAL_FORMATION_TAX_RATE[AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_CRAFTSMAN]
        elif self.professional_category == AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL:
            tax_rate = PROFESSIONAL_FORMATION_TAX_RATE[AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL]

        return tax_rate

    def get_tax_rate(self, reference_date=None, period_is_only_overrun=False):
        tax_rate = 0
        if not self.activity:
            return tax_rate
        today = reference_date or datetime.date.today()

        freeing_tax_payment = self.freeing_tax_payment

        one_year_back = datetime.date(today.year - 1, today.month, today.day)
        first_year = True
        if one_year_back.year >= self.creation_date.year:
            first_year = False

        paid_previous_year = 0
        limit_previous_year = 0
        if not first_year:
            paid_previous_year = Invoice.objects.get_paid_sales(owner=self.user,
                                                                year=one_year_back.year)
            limit_previous_year = self.get_sales_limit(year=one_year_back.year)

        if not first_year and paid_previous_year > limit_previous_year:
            freeing_tax_payment = False

        paid = Invoice.objects.get_paid_sales(owner=self.user)
        limit = self.get_sales_limit()

        if paid > limit:
            freeing_tax_payment = False

        if not period_is_only_overrun and self.creation_help:
            year = self.creation_date.year + 1
            month = self.get_quarter(self.creation_date)[0] * 3 - 1
            first_period_end_date = datetime.date(year, month, 1) - datetime.timedelta(1)
            second_period_end_date = datetime.date(first_period_end_date.year + 1,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            third_period_end_date = datetime.date(first_period_end_date.year + 2,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            if today <= first_period_end_date:
                if freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][0]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][0]
            elif today <= second_period_end_date:
                if freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][1]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][1]
            elif today <= third_period_end_date:
                if freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][2]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][2]

            else:
                if freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]
        else:
            if freeing_tax_payment:
                tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
            else:
                tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]

        if today.year >= 2011:
            tax_rate = tax_rate + self.get_professional_training_tax_rate()

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

    def get_extra_taxes(self, paid, amount_paid_for_tax):
        extra_taxes = 0
        today = datetime.date.today()
        limit = self.get_sales_limit()

        if paid > limit:
            overrun = paid - limit
            if amount_paid_for_tax > overrun:
                tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]
                if today.year >= 2011:
                    tax_rate = tax_rate + self.get_professional_training_tax_rate()
                tax_rate = tax_rate - self.get_tax_rate()
                extra_taxes = float(overrun) * float(tax_rate) / 100

        return extra_taxes

def user_post_save(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        address = Address()
        address.save(user=instance)
        profile = UserProfile()
        profile.user = instance
        profile.address = address
        profile.save()

        today = datetime.date.today()
        subscription = Subscription.objects.create(owner=instance,
                                                   state=SUBSCRIPTION_STATE_TRIAL,
                                                   expiration_date=today + datetime.timedelta(settings.TRIAL_DURATION),
                                                   transaction_id='TRIAL-%i%i%i-%i' % (today.year, today.month, today.day, instance.id))

def log_registration(sender, user, request, **kwargs):
    logger = logging.getLogger('aemanager')
    logger.info('%s <%s> has registered' % (user.username, user.email))

post_save.connect(user_post_save, sender=User)
user_registered.connect(log_registration)
