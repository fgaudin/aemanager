from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext
from core.forms import UserForm, PasswordForm
from autoentrepreneur.forms import UserProfileForm
from contact.forms import AddressForm
from django.db.transaction import commit_on_success
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from accounts.models import Expense, Invoice
from core.decorators import settings_required
from autoentrepreneur.models import AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, \
    Subscription, SUBSCRIPTION_STATE_NOT_PAID, SUBSCRIPTION_STATE_PAID
from project.models import Proposal
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from autoentrepreneur.decorators import subscription_required
from django.contrib.auth import logout
from django.core.mail import mail_admins
from announcement.models import Announcement
import time
import datetime
import urllib, urllib2
from django.conf import settings

@settings_required
@subscription_required
def index(request):
    user = request.user
    profile = user.get_profile()

    if not Proposal.objects.filter(owner=user).count():
        messages.info(request, _('How-to : create a customer, a project, a proposal and finally an invoice'))

    today = datetime.date.today()
    one_year_back = datetime.date(today.year - 1, today.month, today.day)
    first_year = True
    if one_year_back.year >= profile.creation_date.year:
        first_year = False

    service_paid = 0
    service_waiting = 0
    service_to_be_invoiced = 0
    service_limit = 0
    service_paid_previous_year = 0
    service_limit_previous_year = 0

    paid = Invoice.objects.get_paid_sales(owner=user)

    if not first_year:
        paid_previous_year = Invoice.objects.get_paid_sales(owner=user, year=one_year_back.year)
    waiting = Invoice.objects.get_waiting_payments(owner=user)
    to_be_invoiced = Invoice.objects.get_to_be_invoiced(owner=user)
    limit = profile.get_sales_limit()

    if user.get_profile().activity == AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC:
        service_waiting = Invoice.objects.get_waiting_service_payments(owner=user)
        service_to_be_invoiced = Invoice.objects.get_service_to_be_invoiced(owner=user)
        service_limit = profile.get_service_sales_limit()
        service_paid = Invoice.objects.get_paid_service_sales(owner=user)
    if not first_year:
        limit_previous_year = profile.get_sales_limit(year=one_year_back.year)
        if user.get_profile().activity == AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC:
            service_limit_previous_year = profile.get_service_sales_limit(year=one_year_back.year)
            service_paid_previous_year = Invoice.objects.get_paid_service_sales(owner=user, year=one_year_back.year)
    late_invoices = Invoice.objects.get_late_invoices(owner=user)
    invoices_to_send = Invoice.objects.get_invoices_to_send(owner=user)
    potential = Proposal.objects.get_potential_sales(owner=user)
    duration = Proposal.objects.get_potential_duration(owner=user)
    proposals_to_send = Proposal.objects.get_proposals_to_send(owner=user)
    begin_date, end_date = profile.get_period_for_tax()
    amount_paid_for_tax = Invoice.objects.get_paid_sales_for_period(user, begin_date, end_date)
    tax_rate = profile.get_tax_rate()
    amount_to_pay = float(amount_paid_for_tax) * float(tax_rate) / 100

    pay_date = profile.get_pay_date(end_date)

    next_begin_date, next_end_date = profile.get_period_for_tax(pay_date + datetime.timedelta(1))
    next_pay_date = profile.get_pay_date(next_end_date)
    next_amount_paid_for_tax = Invoice.objects.get_paid_sales_for_period(user, next_begin_date, next_end_date)
    next_tax_rate = profile.get_tax_rate(next_begin_date)
    next_amount_to_pay = float(next_amount_paid_for_tax) * float(next_tax_rate) / 100

    min_date = Invoice.objects.get_first_invoice_paid_date(owner=user)
    if not min_date:
        chart_begin_date = today
    elif min_date < one_year_back:
        chart_begin_date = one_year_back
    else:
        chart_begin_date = min_date
    invoices = Invoice.objects.get_paid_invoices(user, begin_date=chart_begin_date)
    sales_progression = []
    last = 0.0
    for invoice in invoices:
        amount = last + float(invoice.amount)
        sales_progression.append([int(time.mktime(invoice.paid_date.timetuple())*1000), amount])
        last = amount

    sales_progression.append([int(time.mktime(today.timetuple())*1000), last])

    waiting_progression = []
    waiting_progression.append([int(time.mktime(today.timetuple())*1000), last])
    waiting_invoices = Invoice.objects.get_waiting_invoices(owner=user)
    for invoice in waiting_invoices:
        amount = last + float(invoice.amount)
        waiting_progression.append([int(time.mktime(invoice.payment_date.timetuple())*1000), amount])
        last = amount

    expenses_progression = []
    last = 0.0
    for expense in Expense.objects.filter(date__gte=chart_begin_date,
                                          owner=user).order_by(('date')):
        amount = last + float(expense.amount)
        expenses_progression.append([int(time.mktime(expense.date.timetuple())*1000), amount])
        last = amount

    expenses_progression.append([int(time.mktime(today.timetuple())*1000), last])

    profit_progression = []
    if len(sales_progression) and len(expenses_progression):
        invoice_counter = 0
        expense_counter = 0
        current_invoice = None
        current_expense = None
        invoice_amount = 0.0
        expense_amount = 0.0
        while invoice_counter < len(sales_progression) and expense_counter < len(expenses_progression):
            current_invoice = sales_progression[invoice_counter]
            current_expense = expenses_progression[expense_counter]
            if current_invoice[0] < current_expense[0]:
                invoice_amount = current_invoice[1]
                profit_progression.append([current_invoice[0], invoice_amount - expense_amount])
                invoice_counter = invoice_counter + 1
            else:
                expense_amount = current_expense[1]
                profit_progression.append([current_expense[0], invoice_amount - expense_amount])
                expense_counter = expense_counter + 1

    sales = {'paid': paid,
             'service_paid': service_paid,
             'waiting': waiting,
             'service_waiting': service_waiting,
             'to_be_invoiced': to_be_invoiced,
             'service_to_be_invoiced': service_to_be_invoiced,
             'total': paid + waiting + to_be_invoiced,
             'service_total': service_paid + service_waiting + service_to_be_invoiced,
             'limit': limit,
             'service_limit': service_limit,
             'remaining': limit - paid - waiting - to_be_invoiced,
             'service_remaining': service_limit - service_paid - service_waiting - service_to_be_invoiced}

    sales_previous_year = None
    if not first_year:
        sales_previous_year = {'paid': paid_previous_year,
                               'service_paid': service_paid_previous_year,
                               'limit': limit_previous_year,
                               'service_limit': service_limit_previous_year,
                               'remaining': limit_previous_year - paid_previous_year,
                               'service_remaining': service_limit_previous_year - service_paid_previous_year}

    invoices = {'late': late_invoices,
                'to_send': invoices_to_send}

    percentage_of_remaining = 0
    if sales['remaining']:
        percentage_of_remaining = potential * 100 / sales['remaining']

    average_unit_price = 0
    if duration:
        average_unit_price = potential / duration

    prospects = {'potential_sales': potential,
                 'percentage_of_remaining': percentage_of_remaining,
                 'duration': duration,
                 'average_unit_price': average_unit_price,
                 'proposals_to_send': proposals_to_send}

    taxes = {'period_begin': begin_date,
             'period_end': end_date,
             'paid_sales_for_period': amount_paid_for_tax,
             'tax_rate': tax_rate,
             'amount_to_pay': amount_to_pay,
             'tax_due_date': pay_date}

    next_taxes = {'period_begin': next_begin_date,
                  'period_end': next_end_date,
                  'paid_sales_for_period': next_amount_paid_for_tax,
                  'tax_rate': next_tax_rate,
                  'amount_to_pay': next_amount_to_pay,
                  'tax_due_date': next_pay_date}

    charts = {'sales_progression':simplejson.dumps(sales_progression),
              'waiting_progression':simplejson.dumps(waiting_progression),
              'expenses_progression':simplejson.dumps(expenses_progression),
              'profit_progression':simplejson.dumps(profit_progression)}

    announcements = Announcement.objects.filter(enabled=True)

    return render_to_response('core/index.html',
                              {'active': 'dashboard',
                               'title': _('Dashboard'),
                               'announcements': announcements,
                               'sales': sales,
                               'sales_previous_year': sales_previous_year,
                               'years': [today.year, today.year - 1],
                               'invoices': invoices,
                               'prospects': prospects,
                               'taxes': taxes,
                               'next_taxes': next_taxes,
                               'charts': charts},
                              context_instance=RequestContext(request))

@login_required
@commit_on_success
def settings_edit(request):
    user = request.user
    profile = user.get_profile()
    address = profile.address

    if request.method == 'POST':
        userform = UserForm(request.POST, prefix="user", instance=user)
        profileform = UserProfileForm(request.POST, prefix="profile", instance=profile)
        addressform = AddressForm(request.POST, prefix="address", instance=address)

        if userform.is_valid() and profileform.is_valid() and addressform.is_valid():
            userform.save()
            profileform.save()
            address = addressform.save(commit=False)
            address.save(user=user)
            messages.success(request, _('Your settings have been updated successfully'))
            return redirect(reverse('settings_edit'))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        userform = UserForm(prefix="user", instance=user)
        profileform = UserProfileForm(prefix="profile", instance=profile)
        addressform = AddressForm(prefix="address", instance=address)

    return render_to_response('core/settings_edit.html',
                              {'active': 'account',
                               'title': _('Settings'),
                               'userform': userform,
                               'profileform': profileform,
                               'addressform': addressform},
                              context_instance=RequestContext(request))

@login_required
@commit_on_success
def change_password(request):
    user = request.user
    if request.method == 'POST':
        passwordform = PasswordForm(request.POST)
        if passwordform.is_valid():
            if user.check_password(passwordform.cleaned_data.get('current_password')):
                user.set_password(passwordform.cleaned_data.get('new_password'))
                user.save()
                messages.success(request, _('Your password has been modified successfully'))
            else:
                messages.error(request, _('Wrong password'))
        else:
            messages.error(request, _('Your password has not been modified'))
    else:
        passwordform = PasswordForm()

    return render_to_response('core/change_password.html',
                              {'active': 'account',
                               'title': _('Change password'),
                               'passwordform': passwordform},
                              context_instance=RequestContext(request))

@login_required
def subscribe(request):
    profile = request.user.get_profile()
    current_subscription = profile.get_last_subscription()
    expired = False
    if current_subscription.expiration_date < datetime.date.today():
        expired = True
    next_expiration_date = profile.get_next_expiration_date()
    price = round(float(settings.PAYPAL_APP_SUBSCRIPTION_AMOUNT) / 12.0, 2)
    return render_to_response('core/subscribe.html',
                              {'active': 'account',
                               'title': _('My subscription'),
                               'subscription': current_subscription,
                               'expired': expired,
                               'next_expiration_date': next_expiration_date,
                               'price': price,
                               'paypal_url': settings.PAYPAL_URL,
                               'button_id': settings.PAYPAL_BUTTON_ID},
                              context_instance=RequestContext(request))

def subscription_paid(request):
    return render_to_response('core/subscription_paid.html',
                              {'active': 'account',
                               'title': _('Subscription paid')},
                              context_instance=RequestContext(request))

@csrf_exempt
@commit_on_success
def paypal_ipn(request):
    # send back the response to paypal
    data = dict(request.POST.items())
    args = {'cmd': '_notify-validate'}
    args.update(data)
    params = urllib.urlencode(args)
    paypal_response = urllib2.urlopen(settings.PAYPAL_URL + '/cgi-bin/webscr', params).read()

    # process the payment
    receiver_id = data['receiver_id']
    transaction_id = data['txn_id']
    payment_status = data['payment_status']
    payment_amount = data['mc_gross']
    payment_currency = data['mc_currency']
    user_id = data['custom']
    user = get_object_or_404(User, pk=user_id)
    profile = user.get_profile()

    subscription, created = Subscription.objects.get_or_create(transaction_id=transaction_id,
                                                               defaults={'owner': user,
                                                                         'state': SUBSCRIPTION_STATE_NOT_PAID,
                                                                         'expiration_date': profile.get_next_expiration_date(),
                                                                         'transaction_id': transaction_id,
                                                                         'error_message': ugettext('Not verified')})

    if paypal_response == 'VERIFIED':
        if receiver_id <> settings.PAYPAL_RECEIVER_ID:
            subscription.error_message = ugettext('Receiver is not as defined in settings. Spoofing ?')
        elif payment_status <> 'Completed':
            subscription.error_message = ugettext('Payment not completed')
        elif payment_amount <> settings.PAYPAL_APP_SUBSCRIPTION_AMOUNT:
            subscription.error_message = ugettext('Amount altered. Bad guy ?')
        elif payment_currency <> settings.PAYPAL_APP_SUBSCRIPTION_CURRENCY:
            subscription.error_message = ugettext('Amount altered. Bad guy ?')
        else:
            subscription.error_message = ugettext('Paid')
            subscription.state = SUBSCRIPTION_STATE_PAID

        subscription.save()

    return render_to_response('core/paypal_ipn.html',
                              {'active': 'account',
                               'title': _('Subscribe')},
                              context_instance=RequestContext(request))

@login_required
@commit_on_success
def unregister(request):
    profile = request.user.get_profile()

    if request.method == 'POST':
        if request.POST.get('unregister'):
            logout(request)
            profile.unregister()
            return redirect(reverse('index'))
        else:
            return redirect(reverse('subscribe'))

    return render_to_response('core/unregister.html',
                              {'active': 'account',
                               'title': _('Unregister')},
                              context_instance=RequestContext(request))

def csrf_failure(request, reason=""):
    email = "unknown"
    if request.user.is_authenticated():
        email = request.user.email
    else:
        if request.method == 'POST':
            email = request.POST.get('email', 'unknown')

    subject = _('CSRF error')
    message = _("An error occured for %(email)s on %(path)s, reason : %(reason)s") % {'email': email,
                                                                                      'path': request.path,
                                                                                      'reason': reason}
    mail_admins(subject, message)
    response = render_to_response('csrf.html',
                                  {'title': _('Error')},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response

