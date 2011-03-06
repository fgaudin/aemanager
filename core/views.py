import logging
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext, Context
from django.utils.translation import ugettext_lazy as _, ugettext
from core.forms import UserForm, PasswordForm, ResendActivationEmailForm, \
    ContactUsForm
from autoentrepreneur.forms import UserProfileForm
from contact.forms import AddressForm
from django.db.transaction import commit_on_success
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from accounts.models import Expense, Invoice, INVOICE_STATE_PAID, \
    PAYMENT_TYPE_BANK_CARD, InvoiceRow
from core.decorators import settings_required
from autoentrepreneur.models import AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, \
    Subscription, SUBSCRIPTION_STATE_NOT_PAID, SUBSCRIPTION_STATE_PAID
from project.models import Proposal, Project, PROJECT_STATE_FINISHED, \
    PROPOSAL_STATE_BALANCED, ROW_CATEGORY_SERVICE, ProposalRow
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from autoentrepreneur.decorators import subscription_required
from django.contrib.auth import logout
from django.core.mail import mail_admins
from announcement.models import Announcement
from contact.models import Contact, CONTACT_TYPE_COMPANY, Address
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.core.mail.message import EmailMessage
from django.template import loader
from django.contrib.admin.views.decorators import staff_member_required
import time
import datetime
import urllib, urllib2
from django.conf import settings
from registration.models import RegistrationProfile

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
        sales_progression.append([int(time.mktime(invoice.paid_date.timetuple())*1000), last])
        sales_progression.append([int(time.mktime(invoice.paid_date.timetuple())*1000), amount])
        last = amount

    sales_progression.append([int(time.mktime(today.timetuple())*1000), last])

    waiting_progression = []
    waiting_progression.append([int(time.mktime(today.timetuple())*1000), last])
    waiting_invoices = Invoice.objects.get_waiting_invoices(owner=user)
    for invoice in waiting_invoices:
        amount = last + float(invoice.amount)
        payment_date = invoice.payment_date
        if payment_date < today:
            payment_date = today
        waiting_progression.append([int(time.mktime(payment_date.timetuple())*1000), last])
        waiting_progression.append([int(time.mktime(payment_date.timetuple())*1000), amount])
        last = amount

    # adding ten days to see last waiting invoice
    if waiting_progression:
        waiting_progression.append([int((waiting_progression[-1][0] + 86400 * 10 * 1000)), waiting_progression[-1][1]])

    expenses_progression = []
    last = 0.0
    for expense in Expense.objects.filter(date__gte=chart_begin_date,
                                          owner=user).order_by(('date')):
        amount = last + float(expense.amount)
        expenses_progression.append([int(time.mktime(expense.date.timetuple())*1000), last])
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
                if profit_progression:
                    profit_progression.append([current_invoice[0], profit_progression[-1][1]])
                profit_progression.append([current_invoice[0], invoice_amount - expense_amount])
                invoice_counter = invoice_counter + 1
            else:
                expense_amount = current_expense[1]
                if profit_progression:
                    profit_progression.append([current_expense[0], profit_progression[-1][1]])
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

    announcements = Announcement.objects.filter(enabled=True, important=False)
    important_announcements = Announcement.objects.filter(enabled=True, important=True)
    for important_announcement in important_announcements:
        messages.warning(request, important_announcement.content)

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
            profile = profileform.save()
            address = addressform.save(commit=False)
            address.save(user=user)
            messages.success(request, _('Your settings have been updated successfully'))
            if profile.creation_date > datetime.date.today():
                messages.warning(request, _("Creation date is in the future, is this normal ?"))
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

@settings_required
def subscribe(request):
    profile = request.user.get_profile()
    current_subscription = profile.get_last_subscription()
    expired = False
    if current_subscription.expiration_date < datetime.date.today():
        expired = True
    next_expiration_date = profile.get_next_expiration_date()
    price = round(float(settings.PAYPAL_APP_SUBSCRIPTION_AMOUNT) / 12.0, 2)
    not_paid_subscriptions = Subscription.objects.get_not_paid_subscription(request.user)

    return render_to_response('core/subscribe.html',
                              {'active': 'account',
                               'title': _('My subscription'),
                               'subscription': current_subscription,
                               'expired': expired,
                               'next_expiration_date': next_expiration_date,
                               'price': price,
                               'not_paid_subscriptions': not_paid_subscriptions,
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
    fee = data['mc_fee']
    item_name = data['item_name']
    user_id = data['custom']
    user = get_object_or_404(User, pk=user_id)
    profile = user.get_profile()
    last_subscription = profile.get_last_subscription()

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

            # create an invoice for this payment
            # first, get the provider user
            provider = User.objects.get(email=settings.SERVICE_PROVIDER_EMAIL)
            # look for a customer corresponding to user
            address, created = Address.objects.get_or_create(contact__email=user.email,
                                                             owner=provider,
                                                             defaults={'street': profile.address.street,
                                                                       'zipcode': profile.address.zipcode,
                                                                       'city': profile.address.city,
                                                                       'country': profile.address.country,
                                                                       'owner': provider})
            customer, created = Contact.objects.get_or_create(email=user.email,
                                                              defaults={'contact_type': CONTACT_TYPE_COMPANY,
                                                                        'name': '%s %s' % (user.first_name, user.last_name),
                                                                        'company_id': profile.company_id,
                                                                        'legal_form': 'Auto-entrepreneur',
                                                                        'email': user.email,
                                                                        'address': address,
                                                                        'owner': provider})
            # create a related project if needed
            # set it to finished to clear daily business
            project, created = Project.objects.get_or_create(state=PROJECT_STATE_FINISHED,
                                                             customer=customer,
                                                             name='Subscription %s - %s %s' % (Site.objects.get_current().name, user.first_name, user.last_name),
                                                             defaults={'state': PROJECT_STATE_FINISHED,
                                                                       'customer': customer,
                                                                       'name': 'Subscription %s - %s %s' % (Site.objects.get_current().name, user.first_name, user.last_name),
                                                                       'owner': provider})

            # create proposal for this subscription
            begin_date = datetime.date.today()
            if begin_date < last_subscription.expiration_date:
                begin_date = last_subscription.expiration_date

            proposal = Proposal.objects.create(project=project,
                                               reference='subscription-%i%i%i' % (subscription.expiration_date.year,
                                                                                  subscription.expiration_date.month,
                                                                                  subscription.expiration_date.day),
                                               state=PROPOSAL_STATE_BALANCED,
                                               begin_date=begin_date,
                                               end_date=subscription.expiration_date,
                                               contract_content='',
                                               update_date=datetime.date.today(),
                                               expiration_date=None,
                                               owner=provider)
            proposal_row = ProposalRow.objects.create(proposal=proposal,
                                                      label=item_name,
                                                      category=ROW_CATEGORY_SERVICE,
                                                      quantity=1,
                                                      unit_price='%s' % settings.PAYPAL_APP_SUBSCRIPTION_AMOUNT,
                                                      owner=provider)

            # finally create invoice
            invoice = Invoice.objects.create(customer=customer,
                                             invoice_id=Invoice.objects.get_next_invoice_id(provider),
                                             state=INVOICE_STATE_PAID,
                                             amount=payment_amount,
                                             edition_date=datetime.date.today(),
                                             payment_date=datetime.date.today(),
                                             paid_date=datetime.date.today(),
                                             payment_type=PAYMENT_TYPE_BANK_CARD,
                                             execution_begin_date=begin_date,
                                             execution_end_date=subscription.expiration_date,
                                             penalty_date=None,
                                             penalty_rate=None,
                                             discount_conditions=None,
                                             owner=provider)

            invoice_row = InvoiceRow.objects.create(proposal=proposal,
                                                    invoice=invoice,
                                                    label=item_name,
                                                    category=ROW_CATEGORY_SERVICE,
                                                    quantity=1,
                                                    unit_price=payment_amount,
                                                    balance_payments=True,
                                                    owner=provider)
            # create expense for paypal fee
            expense = Expense.objects.create(date=datetime.date.today(),
                                             reference=transaction_id,
                                             supplier='Paypal',
                                             amount=fee,
                                             payment_type=PAYMENT_TYPE_BANK_CARD,
                                             description='Commission paypal',
                                             owner=provider)

            # generate invoice in pdf
            response = HttpResponse(mimetype='application/pdf')
            invoice.to_pdf(provider, response)

            subject_template = loader.get_template('core/subscription_paid_email_subject.html')
            subject_context = {'site_name': Site.objects.get_current().name}
            subject = subject_template.render(Context(subject_context))
            body_template = loader.get_template('core/subscription_paid_email.html')
            body_context = {'site_name': Site.objects.get_current().name,
                            'expiration_date': subscription.expiration_date}
            body = body_template.render(Context(body_context))
            email = EmailMessage(subject=subject,
                                 body=body,
                                 to=[user.email])
            email.attach('facture_%i.pdf' % (invoice.invoice_id), response.content, 'application/pdf')
            email.send(fail_silently=(not settings.DEBUG))

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
            logger = logging.getLogger('aemanager')
            logger.info('%s <%s> has unregistered' % (profile.user.username, profile.user.email))
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
            email = request.POST.get('email', None)
            if not email:
                email = request.POST.get('username', 'unknown')

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

def resend_activation_email(request):
    if request.method == 'POST':
        form = ResendActivationEmailForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            email = cleaned_data['email']
            try:
                profile = RegistrationProfile.objects.get(user__email=email)
                if profile.activation_key_expired():
                    form._errors['email'] = form.error_class([_("Activation key expired. You may already have activated your account. If not, activation delay may have passed, you have to wait for your previous registration to be deleted (max. 1 day).")])
                else:
                    site = Site.objects.get_current()
                    profile.send_activation_email(site)
                    return redirect(reverse('registration_complete'))
            except RegistrationProfile.DoesNotExist:
                form._errors['email'] = form.error_class([_("Email address not found. Activation delay may have expired. Try subscribing again.")])
    else:
        form = ResendActivationEmailForm()
    return render_to_response('core/resend_activation_email.html',
                              {'form': form},
                              context_instance=RequestContext(request))

def contact_us(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            EmailMessage(subject=u'[%s] %s' % (Site.objects.get_current().name, cleaned_data['subject']),
                         body=cleaned_data['message'],
                         from_email=cleaned_data['email'],
                         to=[a[1] for a in settings.MANAGERS]).send(fail_silently=(not settings.DEBUG))
            return redirect(reverse('message_sent'))
    else:
        form = ContactUsForm()
    return render_to_response('core/contact_us.html',
                              {'form': form},
                              context_instance=RequestContext(request))
