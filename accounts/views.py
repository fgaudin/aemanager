from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from accounts.forms import ExpenseForm
from accounts.models import Expense
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.formats import localize
import datetime

def expense_list(request):
    user = request.user
    expenses = Expense.objects.filter(owner=user).order_by('-date')
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
    else:
        form = ExpenseForm(initial={'date': localize(datetime.date.today())})
    return render_to_response('expense/list.html',
                              {'active': 'accounts',
                               'title': _('Expenses'),
                               'form': form,
                               'expenses': expenses},
                              context_instance=RequestContext(request))

def expense_add(request):
    response = {'error': 'ko'}
    if request.POST:
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.owner = request.user
            expense.save()
            response['error'] = 'ok'
            response['id'] = expense.id
            response['date'] = localize(expense.date)
            response['reference'] = expense.reference
            response['amount'] = localize(expense.amount)
            response['payment_type'] = expense.payment_type
            response['payment_type_label'] = expense.get_payment_type_display()
            response['description'] = expense.description
        else:
            response['error_msg'] = []
            for key, msg in form.errors.items():
                response['error_msg'].append("%s : %s" % (unicode(form[key].label), " ".join(msg)))

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

def expense_edit(request):
    id = request.GET.get('id')
    expense = get_object_or_404(Expense, pk=id)
    response = {'error': 'ko'}
    if request.POST:
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save()
            response['error'] = 'ok'
            response['id'] = expense.id
            response['date'] = localize(expense.date)
            response['reference'] = expense.reference
            response['amount'] = localize(expense.amount)
            response['payment_type'] = expense.payment_type
            response['payment_type_label'] = expense.get_payment_type_display()
            response['description'] = expense.description
        else:
            response['error_msg'] = []
            for key, msg in form.errors.items():
                response['error_msg'].append("%s : %s" % (unicode(form[key].label), " ".join(msg)))


    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

def expense_delete(request):
    response = {'error': 'ko'}
    if request.POST:
        id = int(request.POST.get('id'))
        if id:
            Expense.objects.filter(pk=id).delete()
            response['error'] = 'ok'
            response['id'] = id

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')
