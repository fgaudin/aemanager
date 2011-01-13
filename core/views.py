from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from core.forms import UserForm
from autoentrepreneur.forms import UserProfileForm
from contact.forms import AddressForm
from django.db.transaction import commit_on_success
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from accounts.models import Expense
import time
import datetime

@login_required
def index(request):
    user = request.user
    today = datetime.date.today()
    one_year_back = datetime.date(today.year - 1, today.month, today.day)
    first_year = True
    if one_year_back.year >= user.get_profile().creation_date.year:
        first_year = False

    paid = user.get_profile().get_paid_sales()
    if not first_year:
        paid_previous_year = user.get_profile().get_paid_sales(year=one_year_back.year)
    waiting = user.get_profile().get_waiting_payments()
    to_be_invoiced = user.get_profile().get_to_be_invoiced()
    limit = user.get_profile().get_sales_limit()
    if not first_year:
        limit_previous_year = user.get_profile().get_sales_limit(year=one_year_back.year)
    late_invoices = user.get_profile().get_late_invoices()
    invoices_to_send = user.get_profile().get_invoices_to_send()
    potential = user.get_profile().get_potential_sales()
    duration = user.get_profile().get_potential_duration()
    proposals_to_send = user.get_profile().get_proposals_to_send()
    begin_date, end_date = user.get_profile().get_period_for_tax()
    amount_paid_for_tax = user.get_profile().get_paid_sales_for_period(begin_date, end_date)
    tax_rate = user.get_profile().get_tax_rate()
    amount_to_pay = float(amount_paid_for_tax) * float(tax_rate) / 100

    pay_date = user.get_profile().get_pay_date(end_date)

    next_begin_date, next_end_date = user.get_profile().get_period_for_tax(pay_date + datetime.timedelta(1))
    next_pay_date = user.get_profile().get_pay_date(next_end_date)
    next_amount_paid_for_tax = user.get_profile().get_paid_sales_for_period(next_begin_date, next_end_date)
    next_tax_rate = user.get_profile().get_tax_rate(next_begin_date)
    next_amount_to_pay = float(next_amount_paid_for_tax) * float(next_tax_rate) / 100

    min_date = user.get_profile().get_first_invoice_paid_date()
    if min_date < one_year_back:
        chart_begin_date = one_year_back
    else:
        chart_begin_date = min_date
    invoices = user.get_profile().get_paid_invoices(begin_date=chart_begin_date)
    sales_progression = []
    last = 0.0
    for invoice in invoices:
        amount = last + float(invoice.amount)
        sales_progression.append([int(time.mktime(invoice.paid_date.timetuple())*1000), amount])
        last = amount

    sales_progression.append([int(time.mktime(today.timetuple())*1000), last])

    waiting_progression = []
    waiting_progression.append([int(time.mktime(today.timetuple())*1000), last])
    waiting_invoices = user.get_profile().get_waiting_invoices()
    for invoice in waiting_invoices:
        amount = last + float(invoice.amount)
        waiting_progression.append([int(time.mktime(invoice.payment_date.timetuple())*1000), amount])
        last = amount

    expenses_progression = []
    last = 0.0
    for expense in Expense.objects.filter(date__gte=chart_begin_date).order_by(('date')):
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
             'waiting': waiting,
             'to_be_invoiced': to_be_invoiced,
             'total': paid + waiting + to_be_invoiced,
             'limit': limit,
             'remaining': limit - paid - waiting - to_be_invoiced}

    sales_previous_year = None
    if not first_year:
        sales_previous_year = {'paid': paid_previous_year,
                               'limit': limit_previous_year,
                               'remaining': limit_previous_year - paid_previous_year}

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

    return render_to_response('core/index.html',
                              {'active': 'dashboard',
                               'title': _('Dashboard'),
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
